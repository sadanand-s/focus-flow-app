"""
1_Dashboard.py — Live engagement monitoring dashboard with webcam feed.
"""
import streamlit as st
import streamlit.components.v1 as components
import av
import cv2
import time
import threading
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from collections import deque

from utils import apply_theme, require_auth, render_page_header, render_metric_card, get_current_user_id, format_duration
from database import get_db, StudySession, EngagementLog, init_db
from cv_engine import CVProcessor
from troll_system import check_and_trigger
from gemini_utils import generate_realtime_suggestion

try:
    from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
    HAS_WEBRTC = True
except ImportError:
    HAS_WEBRTC = False

st.set_page_config(page_title="Dashboard — Focus Flow", page_icon="🧠", layout="wide")
apply_theme(st.session_state.get("theme", "Dark"))
require_auth()

render_page_header("📹 Live Dashboard", "Real-time engagement monitoring")

# ─── Shared state for live metrics ────────────────────────────────────────────
if 'live_stats' not in st.session_state:
    st.session_state['live_stats'] = {
        'scores': [],
        'timestamps': [],
        'distractions': 0,
        'gaze_scores': [],
        'ear_values': [],
    }

if 'current_session_id' not in st.session_state:
    st.session_state['current_session_id'] = None

if 'distraction_start_time' not in st.session_state:
    st.session_state['distraction_start_time'] = None

if 'session_start_ts' not in st.session_state:
    st.session_state['session_start_ts'] = None


# ─── Video Processor ─────────────────────────────────────────────────────────
class EngagementVideoProcessor(VideoProcessorBase):
    """WebRTC video processor for real-time engagement detection."""

    def __init__(self):
        self.processor = CVProcessor()
        self.latest_result = {}
        self.lock = threading.Lock()
        self._frame_count = 0
        self._log_interval = 15  # Log every 15 frames (~0.5s at 30fps)

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        results = self.processor.process_frame(img)

        with self.lock:
            self.latest_result = results
            self._frame_count += 1

        # Log to database periodically
        if (self._frame_count % self._log_interval == 0 and
                st.session_state.get('current_session_id')):
            try:
                db = next(get_db())
                log = EngagementLog(
                    session_id=st.session_state['current_session_id'],
                    ear_value=results.get('ear', 0.0),
                    head_pitch=results.get('pitch', 0.0),
                    head_yaw=results.get('yaw', 0.0),
                    head_roll=results.get('roll', 0.0),
                    gaze_score=results.get('gaze_score', 0.0),
                    expression_score=results.get('expression_score', 1.0),
                    presence_score=results.get('presence_score', 0.0),
                    engagement_score=results.get('engagement_score', 0.0),
                    is_distracted=results.get('is_distracted', False),
                    is_spoof=results.get('is_spoof', False),
                )
                db.add(log)
                db.commit()
                db.close()
            except Exception:
                pass

        return av.VideoFrame.from_ndarray(results.get('annotated_frame', img), format="bgr24")

    def get_latest(self):
        with self.lock:
            return dict(self.latest_result)


# ─── Layout ──────────────────────────────────────────────────────────────────
col_feed, col_controls = st.columns([3, 2])

with col_controls:
    st.subheader("🎮 Session Controls")

    if st.session_state['current_session_id'] is None:
        # Create new session
        with st.form("new_session_form", clear_on_submit=True):
            session_name = st.text_input("📝 Session Name", "Study Session")
            tag = st.selectbox("🏷️ Subject Tag",
                               ["General", "Math", "Science", "Programming",
                                "Reading", "Writing", "History", "Languages", "Other"])
            start_btn = st.form_submit_button("▶️ Start Session", type="primary",
                                               use_container_width=True)

            if start_btn and session_name:
                try:
                    db = next(get_db())
                    user_id = get_current_user_id(db)
                    new_session = StudySession(
                        user_id=user_id,
                        name=session_name,
                        tag=tag,
                        status="active",
                    )
                    db.add(new_session)
                    db.commit()
                    db.refresh(new_session)

                    st.session_state['current_session_id'] = new_session.id
                    st.session_state['session_start_ts'] = time.time()
                    st.session_state['live_stats'] = {
                        'scores': [], 'timestamps': [],
                        'distractions': 0, 'gaze_scores': [],
                        'ear_values': [],
                    }
                    db.close()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create session: {e}")
    else:
        # Active session
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0,210,106,0.1), rgba(0,210,106,0.05));
            border: 1px solid rgba(0,210,106,0.3); border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
            <div style="color: #00D26A; font-weight: 600; font-size: 1rem;">
                🟢 Session Active (ID: {st.session_state['current_session_id']})
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Duration
        if st.session_state.get('session_start_ts'):
            elapsed = time.time() - st.session_state['session_start_ts']
            st.caption(f"⏱️ Duration: {format_duration(elapsed)}")

        if st.button("⏹️ End Session", type="primary", use_container_width=True):
            try:
                db = next(get_db())
                session = db.query(StudySession).filter(
                    StudySession.id == st.session_state['current_session_id']
                ).first()
                if session:
                    session.end_time = datetime.utcnow()
                    session.status = "completed"
                    if st.session_state.get('session_start_ts'):
                        session.duration_seconds = int(time.time() - st.session_state['session_start_ts'])

                    stats = st.session_state['live_stats']
                    if stats['scores']:
                        session.avg_engagement = sum(stats['scores']) / len(stats['scores'])
                        session.peak_engagement = max(stats['scores'])
                    session.total_distractions = stats.get('distractions', 0)

                    db.commit()

                st.session_state['current_session_id'] = None
                st.session_state['session_start_ts'] = None
                db.close()
                st.success("✅ Session ended! View it in the Sessions page.")
                st.rerun()
            except Exception as e:
                st.error(f"Error ending session: {e}")

    st.divider()

    # ─── Live Metrics ─────────────────────────────────────────────
    st.subheader("📊 Live Metrics")

    stats = st.session_state['live_stats']
    if stats['scores']:
        avg_score = sum(stats['scores'][-30:]) / len(stats['scores'][-30:])  # Last 30 readings
        current_score = stats['scores'][-1] if stats['scores'] else 0

        m1, m2 = st.columns(2)
        with m1:
            render_metric_card("Current", f"{current_score:.0f}%", "🎯")
        with m2:
            render_metric_card("Average", f"{avg_score:.0f}%", "📊")

        st.markdown("<br>", unsafe_allow_html=True)

        m3, m4 = st.columns(2)
        with m3:
            render_metric_card("Distractions", f"{stats['distractions']}", "⚡")
        with m4:
            if st.session_state.get('session_start_ts'):
                dur = format_duration(time.time() - st.session_state['session_start_ts'])
            else:
                dur = "0s"
            render_metric_card("Duration", dur, "⏱️")
    else:
        st.info("📹 Start a session and enable webcam to see live metrics.")


with col_feed:
    st.subheader("📹 Live Feed")

    if HAS_WEBRTC:
        ctx = webrtc_streamer(
            key="engagement_feed",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=EngagementVideoProcessor,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        # Update live stats from processor
        if ctx.video_processor:
            latest = ctx.video_processor.get_latest()
            if latest and latest.get('has_face') is not None:
                score = latest.get('engagement_score', 0)
                st.session_state['live_stats']['scores'].append(score)
                st.session_state['live_stats']['timestamps'].append(time.time())
                if latest.get('gaze_score') is not None:
                    st.session_state['live_stats']['gaze_scores'].append(latest['gaze_score'])
                if latest.get('ear') is not None:
                    st.session_state['live_stats']['ear_values'].append(latest['ear'])
                if latest.get('is_distracted', False):
                    st.session_state['live_stats']['distractions'] += 1

                    # Track distraction duration for trolls
                    if st.session_state.get('distraction_start_time') is None:
                        st.session_state['distraction_start_time'] = time.time()
                else:
                    st.session_state['distraction_start_time'] = None

                # Spoof warning
                if latest.get('is_spoof', False):
                    st.warning("⚠️ **Static Image Detected!** The system detected you may be using a photo. This will be noted in your report.")

        # Troll/Nudge check
        if st.session_state.get('distraction_start_time'):
            dist_secs = time.time() - st.session_state['distraction_start_time']
            troll_result = check_and_trigger(
                dist_secs,
                sensitivity=st.session_state.get('nudge_sensitivity', 'Medium'),
                troll_mode=st.session_state.get('troll_mode', True),
                nudge_only=st.session_state.get('nudge_only', False),
            )
            if troll_result['should_trigger']:
                components.html(troll_result['html'], height=300, scrolling=False)

                # Gemini real-time suggestion
                api_key = st.session_state.get('gemini_api_key', '')
                if api_key:
                    suggestion = generate_realtime_suggestion(api_key, {
                        'distraction_minutes': dist_secs / 60,
                        'engagement': st.session_state['live_stats']['scores'][-1] if st.session_state['live_stats']['scores'] else 0,
                        'session_minutes': (time.time() - st.session_state.get('session_start_ts', time.time())) / 60,
                        'subject': 'General',
                        'total_distractions': st.session_state['live_stats']['distractions'],
                    })
                    st.info(f"🤖 **AI Coach:** {suggestion}")
    else:
        st.warning("⚠️ `streamlit-webrtc` is not available. Install it with `pip install streamlit-webrtc` for live webcam support.")
        st.info("In the meantime, check out the **Demo** page for a simulated session!")

# ─── Real-time Chart ──────────────────────────────────────────────────────────
st.divider()
st.subheader("📈 Engagement Timeline")

stats = st.session_state['live_stats']
if len(stats['scores']) > 2:
    chart_df = pd.DataFrame({
        'Time': pd.to_datetime(stats['timestamps'][-100:], unit='s'),
        'Engagement': stats['scores'][-100:],
    })
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chart_df['Time'], y=chart_df['Engagement'],
        mode='lines', name='Engagement %',
        line=dict(color='#FF4B4B', width=2),
        fill='tozeroy', fillcolor='rgba(255,75,75,0.1)',
    ))
    fig.add_hline(y=60, line_dash="dot", line_color="#00D26A", annotation_text="Focus Threshold")
    fig.update_layout(
        yaxis=dict(range=[0, 105]),
        template="plotly_dark", height=300,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("📊 Engagement data will appear here once the session starts.")
