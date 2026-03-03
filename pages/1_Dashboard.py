"""
1_Dashboard.py — Live engagement monitoring dashboard with webcam feed.
Fixed: WebRTC initialization, session DB handling, spoof detection escalation,
       troll system integration, distraction tracking.
"""
import streamlit as st
import streamlit.components.v1 as components
import time
import threading
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from utils import apply_theme, require_auth, render_page_header, render_metric_card, get_current_user_id, format_duration
from database import get_db, StudySession, EngagementLog, init_db
from troll_system import check_and_trigger

# ─── WebRTC Import (graceful fallback) ───────────────────────────────────────
try:
    import av
    import cv2
    from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode, RTCConfiguration
    from cv_engine import CVProcessor
    HAS_WEBRTC = True
except ImportError as _e:
    HAS_WEBRTC = False
    _WEBRTC_ERR = str(_e)

# ─── Page Setup ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dashboard — Focus Flow", page_icon="🧠", layout="wide")
apply_theme(st.session_state.get("theme", "Dark"))
require_auth()

render_page_header("📹 Live Dashboard", "Real-time engagement monitoring")

# ─── Session State Defaults ──────────────────────────────────────────────────
for _k, _v in {
    'live_stats': {'scores': [], 'timestamps': [], 'distractions': 0,
                   'gaze_scores': [], 'ear_values': []},
    'current_session_id': None,
    'distraction_start_time': None,
    'session_start_ts': None,
    'spoof_count': 0,
    'spoof_banner_dismissed': False,
    'spoof_banner_dismissed_at': 0,
    'last_troll_time': 0,
    'mood_checked': False,
    'mood_score': None,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─── Mood Check-In (before session starts) ───────────────────────────────────
@st.dialog("How are you feeling? 😊")
def mood_checkin():
    st.markdown("Quick check-in before your session:")
    col1, col2, col3, col4, col5 = st.columns(5)
    mood_emojis = ["😴", "😐", "🙂", "😄", "🤩"]
    mood_labels = ["Sleepy", "Meh", "Okay", "Good", "Pumped!"]
    for i, (col, emoji, label) in enumerate(zip([col1,col2,col3,col4,col5], mood_emojis, mood_labels)):
        with col:
            if st.button(f"{emoji}\n{label}", key=f"mood_{i}", use_container_width=True):
                st.session_state['mood_score'] = i + 1
                st.session_state['mood_checked'] = True
                st.rerun()


# ─── WebRTC Video Processor ──────────────────────────────────────────────────
if HAS_WEBRTC:
    class EngagementVideoProcessor(VideoProcessorBase):
        """WebRTC video processor for real-time engagement detection."""

        def __init__(self):
            self.processor = CVProcessor()
            self.latest_result = {}
            self.lock = threading.Lock()
            self._frame_count = 0
            self._log_interval = 30  # Log ~every 1 second at 30fps

        def recv(self, frame):
            img = frame.to_ndarray(format="bgr24")
            try:
                results = self.processor.process_frame(img)
            except Exception:
                results = {'annotated_frame': img, 'engagement_score': 0,
                           'has_face': False, 'is_distracted': False, 'is_spoof': False}

            with self.lock:
                self.latest_result = results
                self._frame_count += 1

            annotated = results.get('annotated_frame', img)
            return av.VideoFrame.from_ndarray(annotated, format="bgr24")

        def get_latest(self):
            with self.lock:
                return dict(self.latest_result)

    # STUN servers for WebRTC connectivity
    RTC_CONFIG = RTCConfiguration({
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
        ]
    })


# ─── Layout ──────────────────────────────────────────────────────────────────
col_feed, col_controls = st.columns([3, 2])

# ── Session Controls ─────────────────────────────────────────────────────────
with col_controls:
    st.subheader("🎮 Session Controls")

    if st.session_state['current_session_id'] is None:
        # Mood check-in prompt
        if not st.session_state.get('mood_checked'):
            mood_col1, mood_col2 = st.columns([2, 1])
            with mood_col1:
                st.info("💭 Quick mood check before starting?")
            with mood_col2:
                if st.button("📝 Check In", key="open_mood"):
                    mood_checkin()

        # Create new session form
        with st.form("new_session_form", clear_on_submit=True):
            session_name = st.text_input("📝 Session Name", "Study Session",
                                          placeholder="e.g. Math Exam Prep")
            tag = st.selectbox("🏷️ Subject Tag",
                               ["General", "Math", "Science", "Programming",
                                "Reading", "Writing", "History", "Languages", "Other"])
            start_btn = st.form_submit_button("▶️ Start Session", type="primary",
                                               use_container_width=True)

            if start_btn:
                if not session_name.strip():
                    st.warning("Please enter a session name.")
                else:
                    try:
                        db = next(get_db())
                        user_id = get_current_user_id(db)
                        new_session = StudySession(
                            user_id=user_id,
                            name=session_name.strip(),
                            tag=tag,
                            status="active",
                        )
                        db.add(new_session)
                        db.commit()
                        db.refresh(new_session)

                        sid = new_session.id
                        db.close()

                        st.session_state['current_session_id'] = sid
                        st.session_state['session_start_ts'] = time.time()
                        st.session_state['live_stats'] = {
                            'scores': [], 'timestamps': [],
                            'distractions': 0, 'gaze_scores': [],
                            'ear_values': [],
                        }
                        st.session_state['spoof_count'] = 0
                        st.session_state['distraction_start_time'] = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create session: {e}")
    else:
        # Active session card
        session_dur = ""
        if st.session_state.get('session_start_ts'):
            elapsed = time.time() - st.session_state['session_start_ts']
            session_dur = format_duration(elapsed)

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0,230,118,0.1), rgba(0,210,255,0.05));
            border: 1px solid rgba(0,230,118,0.25); border-radius: 12px;
            padding: 1rem; margin-bottom: 1rem;">
            <div style="color: #00E676; font-weight: 700; font-size: 1rem; margin-bottom: 4px;">
                🟢 Session Active
            </div>
            <div style="color: #9E9E9E; font-size: 0.85rem;">
                ID: #{st.session_state['current_session_id']} &nbsp;·&nbsp; ⏱️ {session_dur}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.get('mood_score'):
            mood_emoji = ["😴", "😐", "🙂", "😄", "🤩"][st.session_state['mood_score'] - 1]
            st.caption(f"Pre-session mood: {mood_emoji}")

        if st.button("⏹️ End Session", type="primary", use_container_width=True, key="end_session"):
            try:
                db = next(get_db())
                session = db.query(StudySession).filter(
                    StudySession.id == st.session_state['current_session_id']
                ).first()
                if session:
                    session.end_time = datetime.now()
                    session.status = "completed"
                    if st.session_state.get('session_start_ts'):
                        session.duration_seconds = int(
                            time.time() - st.session_state['session_start_ts'])

                    stats = st.session_state['live_stats']
                    if stats['scores']:
                        session.avg_engagement = float(
                            sum(stats['scores']) / len(stats['scores']))
                        session.peak_engagement = float(max(stats['scores']))
                    session.total_distractions = int(stats.get('distractions', 0))
                    session.spoof_detected = st.session_state.get('spoof_count', 0) > 0
                    db.commit()

                db.close()
                st.session_state['current_session_id'] = None
                st.session_state['session_start_ts'] = None
                st.session_state['mood_checked'] = False
                st.session_state['mood_score'] = None
                st.success("✅ Session ended! View it in the Sessions page.")
                st.rerun()
            except Exception as e:
                st.error(f"Error ending session: {e}")

    st.divider()

    # ─── Live Metrics ─────────────────────────────────────────────
    st.subheader("📊 Live Metrics")

    stats = st.session_state['live_stats']
    if stats['scores']:
        recent = stats['scores'][-30:]
        current_score = stats['scores'][-1]
        avg_score = sum(recent) / len(recent)

        # Color-coded score gauge
        score_color = "#00E676" if current_score >= 70 else ("#FFD600" if current_score >= 40 else "#FF5252")
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:1rem;">
            <div style="font-size:3rem;font-weight:900;color:{score_color};
                text-shadow:0 0 20px {score_color}44;
                font-family:'JetBrains Mono',monospace;">
                {current_score:.0f}%
            </div>
            <div style="color:#9E9E9E;font-size:0.85rem;">Current Engagement</div>
        </div>
        """, unsafe_allow_html=True)

        m1, m2 = st.columns(2)
        with m1:
            render_metric_card("Avg (30s)", f"{avg_score:.0f}%", "📊")
        with m2:
            render_metric_card("Distractions", f"{stats['distractions']}", "⚡")

        st.markdown("<br>", unsafe_allow_html=True)

        m3, m4 = st.columns(2)
        with m3:
            dur = format_duration(time.time() - st.session_state['session_start_ts']) if st.session_state.get('session_start_ts') else "0s"
            render_metric_card("Duration", dur, "⏱️")
        with m4:
            peak = max(stats['scores']) if stats['scores'] else 0
            render_metric_card("Peak", f"{peak:.0f}%", "🏆")
    else:
        st.info("📹 Start a session and enable your webcam to see live metrics.")
        if not HAS_WEBRTC:
            st.warning("⚠️ `streamlit-webrtc` is not installed. Run: `pip install streamlit-webrtc av`")


# ── Webcam Feed ───────────────────────────────────────────────────────────────
with col_feed:
    st.subheader("📹 Live Feed")

    if not HAS_WEBRTC:
        st.error(f"""
        **Camera unavailable** — `streamlit-webrtc` or `av` package is missing.

        Install with:
        ```bash
        pip install streamlit-webrtc av opencv-python-headless
        ```
        """)
    else:
        # Spoof banner (shown outside the webrtc widget area)
        spoof_count = st.session_state.get('spoof_count', 0)
        dismissed_at = st.session_state.get('spoof_banner_dismissed_at', 0)
        show_banner = spoof_count > 0 and (
            not st.session_state.get('spoof_banner_dismissed') or
            (time.time() - dismissed_at) > 60
        )
        if show_banner:
            bcol1, bcol2 = st.columns([8, 1])
            with bcol1:
                st.warning("⚠️ **Static image detected.** FocusTrack needs your real face to work accurately.")
            with bcol2:
                if st.button("✕", key="dismiss_spoof"):
                    st.session_state['spoof_banner_dismissed'] = True
                    st.session_state['spoof_banner_dismissed_at'] = time.time()
                    st.rerun()

        # WebRTC streamer
        ctx = webrtc_streamer(
            key="engagement_feed",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTC_CONFIG,
            video_processor_factory=EngagementVideoProcessor,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        if ctx.video_processor:
            latest = ctx.video_processor.get_latest()
            if latest and 'engagement_score' in latest:
                score = float(latest.get('engagement_score', 0))
                ts = time.time()

                # Update live stats
                st.session_state['live_stats']['scores'].append(score)
                st.session_state['live_stats']['timestamps'].append(ts)
                if latest.get('gaze_score') is not None:
                    st.session_state['live_stats']['gaze_scores'].append(
                        float(latest['gaze_score']))
                if latest.get('ear') is not None:
                    st.session_state['live_stats']['ear_values'].append(
                        float(latest['ear']))

                # Distraction tracking
                if latest.get('is_distracted', False):
                    if st.session_state.get('distraction_start_time') is None:
                        st.session_state['distraction_start_time'] = ts
                    if st.session_state.get('current_session_id'):
                        st.session_state['live_stats']['distractions'] += 1
                else:
                    st.session_state['distraction_start_time'] = None

                # Spoof handling
                if latest.get('is_spoof', False):
                    prev_count = st.session_state.get('spoof_count', 0)
                    st.session_state['spoof_count'] = prev_count + 1
                    sc = st.session_state['spoof_count']

                    if sc == 2:
                        st.toast("📸 Still a photo? Your camera deserves better.", icon="😏")
                    elif sc >= 3:
                        # Show modal via HTML
                        components.html("""
                        <div id="spoof-modal" style="
                            position:fixed;top:0;left:0;width:100%;height:100%;
                            background:rgba(0,0,0,0.7);z-index:99999;
                            display:flex;align-items:center;justify-content:center;">
                          <div style="background:#1A1D27;border:1px solid #FF5252;
                              border-radius:16px;padding:2rem;max-width:400px;text-align:center;
                              color:white;box-shadow:0 0 40px rgba(255,82,82,0.3);">
                            <div style="font-size:3rem;margin-bottom:1rem;">👀</div>
                            <h3 style="color:#FF5252;margin-bottom:1rem;">
                              Static Image Detected 3+ Times
                            </h3>
                            <p style="color:#9E9E9E;margin-bottom:1.5rem;">
                              Your engagement data may not be accurate.
                              This will be noted in your final report.
                            </p>
                            <button onclick="document.getElementById('spoof-modal').remove()"
                              style="background:linear-gradient(135deg,#6C63FF,#00D2FF);
                              color:white;border:none;padding:10px 24px;border-radius:50px;
                              cursor:pointer;font-weight:700;">
                              Got it, I'll fix it
                            </button>
                          </div>
                        </div>
                        """, height=1)

        # Troll / Nudge check
        if st.session_state.get('distraction_start_time') and st.session_state.get('current_session_id'):
            dist_secs = time.time() - st.session_state['distraction_start_time']

            # 5-minute soft nudge banner
            if dist_secs >= 300:
                st.info("💡 You've been away for 5 minutes. A 2-minute stretch might help!")

            # Troll event check
            troll_result = check_and_trigger(
                dist_secs,
                sensitivity=st.session_state.get('nudge_sensitivity', 'Medium'),
                troll_mode=st.session_state.get('troll_mode', True),
                nudge_only=st.session_state.get('nudge_only', False),
            )
            if troll_result['should_trigger'] and troll_result['html']:
                components.html(troll_result['html'], height=300, scrolling=False)

        # Camera help text
        if not ctx.state.playing:
            st.markdown("""
            <div style="background:rgba(108,99,255,0.08);border:1px solid rgba(108,99,255,0.2);
                border-radius:12px;padding:1rem;margin-top:0.5rem;">
                <b>🎥 Camera Tips:</b>
                <ul style="margin:0.5rem 0 0 1rem;color:#9E9E9E;font-size:0.9rem;">
                    <li>Click <b>START</b> above to enable your webcam</li>
                    <li>Allow camera permission when prompted by your browser</li>
                    <li>Make sure no other app is using your camera</li>
                    <li>If camera fails, try refreshing and allowing permission again</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)


# ─── Live Chart ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("📈 Engagement Timeline")

stats = st.session_state['live_stats']
focused_threshold = st.session_state.get('focused_threshold', 70)
distracted_threshold = st.session_state.get('distracted_threshold', 40)

if len(stats['scores']) > 2:
    chart_df = pd.DataFrame({
        'Time': pd.to_datetime(stats['timestamps'][-150:], unit='s'),
        'Engagement': stats['scores'][-150:],
    })
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chart_df['Time'], y=chart_df['Engagement'],
        mode='lines', name='Engagement %',
        line=dict(color='#6C63FF', width=2.5),
        fill='tozeroy', fillcolor='rgba(108,99,255,0.08)',
    ))
    fig.add_hline(y=focused_threshold, line_dash="dot", line_color="#00E676",
                  annotation_text=f"Focused ({focused_threshold}%)",
                  annotation_font_color="#00E676")
    fig.add_hline(y=distracted_threshold, line_dash="dot", line_color="#FF5252",
                  annotation_text=f"Distracted ({distracted_threshold}%)",
                  annotation_font_color="#FF5252")
    fig.update_layout(
        yaxis=dict(range=[0, 105], gridcolor='rgba(255,255,255,0.05)'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,29,39,0.5)',
        height=280,
        margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("📊 Engagement chart will appear once the session starts and webcam is active.")
