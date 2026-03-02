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

from utils import (
    apply_theme, require_auth, render_page_header, 
    render_metric_card, get_current_user_id, format_duration, t
)
from database import get_db, StudySession, EngagementLog, SessionLocal
from cv_engine import CVProcessor
from troll_system import check_and_trigger
from gemini_utils import generate_realtime_suggestion

try:
    from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
    HAS_WEBRTC = True
except ImportError:
    HAS_WEBRTC = False

# ─── Page Config ──────────────────────────────────────────────────────────────
app_name = st.session_state.settings_config.get("app_name", "Focus Flow")
st.set_page_config(page_title=f"{app_name} - Dashboard", page_icon="🧠", layout="wide")
apply_theme()
require_auth()

# ─── Session State ───────────────────────────────────────────────────────────
if 'live_stats' not in st.session_state:
    st.session_state['live_stats'] = {
        'scores': [], 'timestamps': [], 'distractions': 0,
        'gaze_scores': [], 'ear_values': [], 'peak_score': 0, 'peak_frame': None
    }

# ─── Video Processor ─────────────────────────────────────────────────────────
class EngagementVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.processor = CVProcessor()
        self.latest_result = {}
        self.lock = threading.Lock()
        self._frame_count = 0

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        results = self.processor.process_frame(img)
        
        with self.lock:
            self.latest_result = results
            self._frame_count += 1
            
            # Peak Focus Snapshot (Evidence Wall)
            score = results.get('engagement_score', 0)
            if score > st.session_state['live_stats'].get('peak_score', 0):
                st.session_state['live_stats']['peak_score'] = score
                # Store a small thumbnail if needed (base64) - handled in UI loop but can flag here
        
        return av.VideoFrame.from_ndarray(results.get('annotated_frame', img), format="bgr24")

    def get_latest(self):
        with self.lock:
            return dict(self.latest_result)

# ─── Header & Streak ────────────────────────────────────────────────────────
status = "live" if st.session_state.get('current_session_id') else "idle"
render_page_header(f"{t('dashboard')}", f"Live monitoring active. 🔥 Streak: {st.session_state.streak_count} days", status=status)

# ─── Main Layout ────────────────────────────────────────────────────────────
col_feed, col_stats = st.columns([3, 2])

with col_feed:
    # ─── Webcam Feed ────────────────────────────────────────────────────────
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    if HAS_WEBRTC:
        ctx = webrtc_streamer(
            key="engagement_feed",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=EngagementVideoProcessor,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )
        
        if ctx.video_processor:
            latest = ctx.video_processor.get_latest()
            if latest and latest.get('has_face'):
                score = latest.get('engagement_score', 0)
                st.session_state['live_stats']['scores'].append(score)
                st.session_state['live_stats']['timestamps'].append(time.time())
                
                # Handling Distractions & Trolls
                if latest.get('is_distracted', False):
                    st.session_state['live_stats']['distractions'] += 1
                    if 'distraction_start_time' not in st.session_state or st.session_state['distraction_start_time'] is None:
                        st.session_state['distraction_start_time'] = time.time()
                else:
                    st.session_state['distraction_start_time'] = None

                # Spoofing UI
                if latest.get('is_spoof', False):
                    st.error(t('spoof_warn'))
                    st.markdown("""
                        <style>
                        [data-testid="stWebcam"] { border: 4px solid #FF5252 !important; border-radius: 12px; animation: pulseError 1s infinite; }
                        @keyframes pulseError { 0% { box-shadow: 0 0 0 0 rgba(255, 82, 82, 0.7); } 70% { box-shadow: 0 0 0 20px rgba(255, 82, 82, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 82, 82, 0); } }
                        </style>
                    """, unsafe_allow_html=True)
    else:
        st.warning("Webcam not available.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ─── Troll System Trigger ────────────────────────────────────────────────
    if st.session_state.get('distraction_start_time'):
        dist_s = time.time() - st.session_state['distraction_start_time']
        troll = check_and_trigger(dist_s)
        if troll:
            components.html(troll['html'], height=0, width=0)
            if "message" in troll:
                st.toast(troll['message'], icon="🤡")

with col_stats:
    # ─── Controls ───────────────────────────────────────────────────────────
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.write("### 🎮 Controls")
    if st.session_state.get('current_session_id') is None:
        with st.form("new_session"):
            s_name = st.text_input("Session Topic", "Deep Work")
            s_tag = st.selectbox("Subject", ["Coding", "Reading", "Math", "General"])
            if st.form_submit_button(t("start_session"), use_container_width=True):
                # Start Session logic
                db = SessionLocal()
                u_id = get_current_user_id(db)
                sess = StudySession(user_id=u_id, name=s_name, tag=s_tag, status="active")
                db.add(sess)
                db.commit()
                st.session_state['current_session_id'] = sess.id
                st.session_state['session_start_ts'] = time.time()
                db.close()
                st.rerun()
    else:
        duration = format_duration(time.time() - st.session_state.get('session_start_ts', time.time()))
        st.write(f"⏱️ **Active:** {duration}")
        if st.button(t("end_session"), type="primary", use_container_width=True):
            # End session logic
            db = SessionLocal()
            sess = db.query(StudySession).filter(StudySession.id == st.session_state['current_session_id']).first()
            if sess:
                sess.status = "completed"
                sess.end_time = datetime.utcnow()
                sess.duration_seconds = int(time.time() - st.session_state['session_start_ts'])
                if st.session_state['live_stats']['scores']:
                    sess.avg_engagement = np.mean(st.session_state['live_stats']['scores'])
                db.commit()
            st.session_state['current_session_id'] = None
            db.close()
            st.success("Session saved! 🎉")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ─── Premium Metrics Grid ──────────────────────────────────────────────
    cfg = st.session_state.settings_config.get("widgets", {})
    m1, m2 = st.columns(2)
    with m1:
        if cfg.get("engagement", True):
            curr = st.session_state['live_stats']['scores'][-1] if st.session_state['live_stats']['scores'] else 0
            render_metric_card(t("live_metric"), f"{curr:.0f}%", "🎯", "Overall focus score based on AI analysis.")
    with m2:
        if cfg.get("ear", True):
            ear = (st.session_state['live_stats']['ear_values'][-1] if st.session_state['live_stats']['ear_values'] else 0) * 100
            render_metric_card(t("ear"), f"{ear:.1f}%", "👁️", "Percentage of eye alertness (drowsiness check).")

    m3, m4 = st.columns(2)
    with m3:
        if cfg.get("posture", True):
            render_metric_card("Alerts", f"{st.session_state['live_stats']['distractions']}", "⚡", "Total distraction events detected.")
    with m4:
        render_metric_card("Streak", f"{st.session_state.streak_count}", "🔥", "Consecutive days of high focus sessions.")

# ─── Timeline Chart ─────────────────────────────────────────────────────────
if st.session_state.settings_config.get("widgets", {}).get("timeline", True):
    st.divider()
    stats = st.session_state['live_stats']
    if len(stats['scores']) > 5:
        chart_df = pd.DataFrame({
            'Time': pd.to_datetime(stats['timestamps'][-100:], unit='s'),
            'Score': stats['scores'][-100:]
        })
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=chart_df['Time'], y=chart_df['Score'],
            fill='tozeroy', line=dict(color='#6C63FF', width=3),
            name="Engagement"
        ))
        fig.update_layout(
            template="plotly_dark", height=300, 
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(range=[0, 100])
        )
        st.plotly_chart(fig, use_container_width=True)

# ─── AI Progress Agent Bubble ──────────────────────────────────────────────
st.markdown("""
    <div style="position: fixed; bottom: 30px; right: 30px; z-index: 1001;">
        <button onclick="window.parent.postMessage({type: 'open_coach'}, '*')" 
            style="width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #6C63FF, #00D2FF); border: none; box-shadow: 0 10px 20px rgba(0,0,0,0.4); cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 28px;">
            🤖
        </button>
    </div>
""", unsafe_allow_html=True)
