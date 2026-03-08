"""
1_Dashboard.py — Live engagement monitoring dashboard with webcam feed.
Fixed: WebRTC initialization, session DB handling, spoof detection escalation,
       troll system integration, distraction tracking.
"""
import streamlit as st
import time
import threading
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from utils import apply_theme, require_auth, render_page_header, render_metric_card, get_current_user_id, format_duration
from database import get_db, StudySession, init_db, save_engagement_log
from troll_system import check_and_trigger

# ─── WebRTC Import (graceful fallback) ───────────────────────────────────────
try:
    import cv2
except ImportError as _e:
    st.error(f"OpenCV is required for camera processing: {_e}")
    st.stop()

try:
    from cv_engine import CVProcessor
except ImportError as _e:
    st.error(f"Vision engine failed to load: {_e}")
    st.stop()

try:
    import av
    from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode, RTCConfiguration
    HAS_WEBRTC = True
    _WEBRTC_ERR = ""
except ImportError as _e:
    HAS_WEBRTC = False
    _WEBRTC_ERR = str(_e)

# Python 3.14 Compatibility Layer
import sys
IS_314 = sys.version_info.major == 3 and sys.version_info.minor == 14

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
    'current_troll_html': None,
    'troll_expire_at': 0,
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
            # Pick up per-user calibration from session state if available
            calib = st.session_state.get("user_calibration", {})
            self.processor = CVProcessor(user_calibration=calib)
            self.latest_result = {}
            self.lock = threading.Lock()
            self._frame_count = 0

        def recv(self, frame):
            img = frame.to_ndarray(format="bgr24")
            try:
                results = self.processor.process_frame(img)
            except Exception as e:
                results = {
                    'annotated_frame': img, 'engagement_score': 5,
                    'has_face': False, 'is_distracted': False, 'is_spoof': False,
                    'conditions': {'ok': True, 'warnings': []},
                    'error': str(e),
                }

            with self.lock:
                self.latest_result = results
                self._frame_count += 1

            annotated = results.get('annotated_frame', img)
            # Overlay condition warnings directly on the WebRTC frame
            conditions = results.get('conditions', {})
            if not conditions.get('ok', True):
                cv2.putText(annotated, "⚠ CHECK CONDITIONS",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            return av.VideoFrame.from_ndarray(annotated, format="bgr24")

        def get_latest(self):
            with self.lock:
                return dict(self.latest_result)

    # STUN servers for WebRTC connectivity (Google public STUN + fallbacks)
    RTC_CONFIG = RTCConfiguration({
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302"]},
        ]
    })


# ─── Camera Modes ─────────────────────────────────────────────────────────────
CAM_MODES = ["WebRTC (Standard)", "Direct Local (OpenCV)", "Snapshot (Safe Mode)"]
if "cam_mode" not in st.session_state:
    st.session_state["cam_mode"] = CAM_MODES[0]

with st.sidebar:
    st.divider()
    st.subheader("⚙️ Camera Configuration")
    selected_mode = st.radio(
        "Select Engine",
        CAM_MODES,
        help="Use 'Direct Local' if you encounter any issues with WebRTC.",
        index=CAM_MODES.index(st.session_state.get("cam_mode", CAM_MODES[0]))
    )
    st.session_state["cam_mode"] = selected_mode

    with st.sidebar.expander("🛠️ WebRTC Diagnostics"):
        if st.session_state["cam_mode"] == "Direct Local (OpenCV)":
            st.success("✅ Direct Engine Active")
            st.info("Direct mode bypasses browser WebRTC limitations.")
        else:
            if not HAS_WEBRTC:
                st.error("❌ WebRTC Library missing")
            else:
                st.write("Ready to connect...")
        
        st.caption("Tip: Use local IP or localhost for testing.")

    st.divider()

class LocalVideoCapture:
    """Fallback OpenCV capture engine for local Windows dev."""
    def __init__(self):
        self.cap = None
        self.processor = CVProcessor()
        self.is_running = False

    def start(self):
        if not self.cap or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.is_running = True
        return self.cap.isOpened()

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def get_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None



# ─── Layout ──────────────────────────────────────────────────────────────────
col_feed, col_controls = st.columns([3, 2])
ctx = None

# ── Webcam Feed ───────────────────────────────────────────────────────────────
with col_feed:
    st.subheader("📹 Live Feed")

    if st.session_state["cam_mode"] == "WebRTC (Standard)":
        if not HAS_WEBRTC:
            st.error(f"""
            **Camera unavailable** — `streamlit-webrtc` or `av` package is missing.
            Error: `{_WEBRTC_ERR}`
    
            Install with:
            ```bash
            pip install streamlit-webrtc av opencv-python-headless
            ```
            """)
        else:
            # WebRTC streamer — auto-start, shows a clear START button
            st.markdown("""
            <div style="background: rgba(108,99,255,0.08); border: 1px solid rgba(108,99,255,0.2);
                border-radius: 10px; padding: 0.7rem 1rem; margin-bottom: 0.5rem; font-size:0.88rem; color:#9E9E9E;">
                📷 Click <b style="color:#E0E0E0;">START</b> below to allow camera access and begin live analysis.
                Make sure your browser granted camera permission.
            </div>
            """, unsafe_allow_html=True)
            ctx = webrtc_streamer(
                key="engagement_feed",
                mode=WebRtcMode.SENDRECV,
                rtc_configuration=RTC_CONFIG,
                video_processor_factory=EngagementVideoProcessor,
                media_stream_constraints={"video": True, "audio": False},
                async_processing=True,
                translations={
                    "start": "▶ Start Camera",
                    "stop": "⏹ Stop Camera",
                    "select_device": "Choose Camera",
                },
            )
    elif st.session_state["cam_mode"] == "Snapshot (Safe Mode)":
        # ── Snapshot Mode (Streamlit Native) ──────────────────
        st.info("Snapshot mode uses the browser's native camera capture. Click the button to analyze a frame.")
        
        img_file = st.camera_input("Take a snapshot for analysis")
        
        if img_file:
            # Convert uploaded file to OpenCV format
            file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, 1)
            
            if "snapshot_processor" not in st.session_state:
                st.session_state.snapshot_processor = CVProcessor()
            
            results = st.session_state.snapshot_processor.process_frame(frame)
            st.session_state['latest_processor_data'] = results
            
            # Show results
            st.image(results['annotated_frame'], channels="BGR", caption="Analyzed Frame", use_container_width=True)
            if results.get('engagement_score', 0) > 0:
                st.success(f"Engagement Analyzed: {results['engagement_score']}% ({results['engagement_label']})")
                
                # Manual trigger check for Snapshot (Instant check)
                if st.session_state.get('current_session_id'):
                    snapshot_dist_seconds = st.session_state.get("settings_config", {}).get("n_delay", 2)
                    troll_result = check_and_trigger(
                        snapshot_dist_seconds,
                        engagement_score=results['engagement_score'],
                        sensitivity=st.session_state.get('nudge_sensitivity', 'Medium'),
                        troll_mode=st.session_state.get('troll_mode', True),
                        nudge_only=st.session_state.get('nudge_only', False),
                    )
                    if troll_result['should_trigger'] and troll_result['html']:
                        st.markdown(troll_result['html'], unsafe_allow_html=True)
    else:
        # ── Direct Local Mode (OpenCV) ───────────────────────────
        st.info("Direct Local Engine active. Browsers ignore this stream but your local PC processes it directly.")
        
        col_st, col_sp = st.columns([1, 1])
        with col_st:
            start_local = st.button("▶️ Start Camera", type="primary", use_container_width=True)
        with col_sp:
            stop_local = st.button("⏹️ Stop Camera", use_container_width=True)

        img_placeholder = st.empty()
        
        # Local Loop Logic
        if "local_cap" not in st.session_state:
            st.session_state.local_cap = LocalVideoCapture()

        if start_local:
            if st.session_state.local_cap.start():
                st.session_state["local_running"] = True
                st.rerun()
            else:
                st.error("Failed to connect to local camera. Ensure no other app is using it.")

        if stop_local:
            st.session_state.local_cap.stop()
            st.session_state["local_running"] = False
            img_placeholder.info("Camera stopped.")
            st.rerun()

        # Handle Direct Loop in a Fragment to avoid blocking the main UI
        @st.fragment(run_every=0.1) # Fast refresh for local camera
        def render_local_loop():
            if st.session_state.get("local_running", False):
                frame = st.session_state.local_cap.get_frame()
                if frame is not None:
                    results = st.session_state.local_cap.processor.process_frame(frame)
                    st.session_state['latest_processor_data'] = results
                    img_placeholder.image(results['annotated_frame'], channels="BGR", use_container_width=True)
                    
                    # Immediate troll check for local mode
                    if results.get('is_distracted', False):
                        if st.session_state.get('distraction_start_time') is None:
                            st.session_state['distraction_start_time'] = time.time()
                    else:
                        st.session_state['distraction_start_time'] = None

        render_local_loop()

        # Spoof banner
        if st.session_state.get('spoof_count', 0) > 5:
            st.warning("⚠️ **Static image detected.** Please ensure you are visible and moving.")

        if ctx and hasattr(ctx, 'video_processor') and ctx.video_processor:
            latest = ctx.video_processor.get_latest()
            if latest and 'engagement_score' in latest:
                # Auto-sync data to session state for fragment
                st.session_state['latest_processor_data'] = latest

        # Python 3.14 Warning
        if IS_314:
            st.warning("⚠️ **Python 3.14 (Beta) Detected.** Streamlit features like 'Auto-Refresh' and 'WebRTC' may be unstable. If the camera freezes, click: 👇")
            if st.button("🔄 Sync Camera Data", use_container_width=True):
                st.rerun()

        # Camera help text
        if ctx and not ctx.state.playing:
            st.markdown("""
            <div style="background:rgba(108,99,255,0.08);border:1px solid rgba(108,99,255,0.2);
                border-radius:12px;padding:1rem;margin-top:0.5rem;">
                <b>🎥 Camera Tips:</b>
                <ul style="margin:0.5rem 0 0 1rem;color:#9E9E9E;font-size:0.9rem;">
                    <li>Click <b>START</b> above to enable your webcam</li>
                    <li>Allow camera permission in your browser</li>
                    <li>Make sure no other app is using your camera</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

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
                        st.session_state['focus_points'] = 0
                        st.session_state['focus_streak'] = 0
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

    # ─── Live Metrics & Chart Fragment ──────────────────────────────
    @st.fragment(run_every=2)
    def render_live_dashboard():
        st.subheader("📊 Live Metrics")
        
        # Pull latest from processor if active
        latest = None
        if ctx and hasattr(ctx, 'video_processor') and ctx.video_processor:
            latest = ctx.video_processor.get_latest()
        elif st.session_state.get('latest_processor_data'):
            latest = st.session_state['latest_processor_data']

        if latest and 'engagement_score' in latest:
            score = float(latest.get('engagement_score', 0))
            ts = time.time()

            # Update live stats
            st.session_state['live_stats']['scores'].append(score)
            st.session_state['live_stats']['timestamps'].append(ts)
            
            # Keep only last 10 minutes of live data in memory
            if len(st.session_state['live_stats']['scores']) > 600:
                st.session_state['live_stats']['scores'] = st.session_state['live_stats']['scores'][-600:]
                st.session_state['live_stats']['timestamps'] = st.session_state['live_stats']['timestamps'][-600:]

            # Update distractions
            if latest.get('is_distracted', False):
                if st.session_state.get('distraction_start_time') is None:
                    st.session_state['distraction_start_time'] = ts
                    if st.session_state.get('current_session_id'):
                        st.session_state['live_stats']['distractions'] += 1
            else:
                st.session_state['distraction_start_time'] = None
            
            # Spoof handling
            if latest.get('is_spoof', False):
                st.session_state['spoof_count'] = st.session_state.get('spoof_count', 0) + 1
                if st.session_state['spoof_count'] == 3:
                    st.toast("Still a photo? Your camera deserves better.", icon="📷")

            # Persist logs to DB (throttled)
            if st.session_state.get('current_session_id'):
                now = time.time()
                last_log = st.session_state.get("last_log_ts", 0)
                if now - last_log >= 2:
                    metrics = {
                        "ear": latest.get("ear", 0.0),
                        "pitch": latest.get("pitch", 0.0),
                        "yaw": latest.get("yaw", 0.0),
                        "roll": latest.get("roll", 0.0),
                        "gaze_score": latest.get("gaze_score", 0.0),
                        "expression_score": latest.get("expression_score", 1.0),
                        "engagement_score": latest.get("engagement_score", 0.0),
                        "is_distracted": latest.get("is_distracted", False),
                        "is_spoof": latest.get("is_spoof", False),
                    }
                    try:
                        db = next(get_db(st.session_state.get("db_url")))
                        save_engagement_log(db, st.session_state['current_session_id'], metrics)
                        db.close()
                        st.session_state["last_log_ts"] = now
                    except Exception:
                        # Avoid spamming errors in the UI; just skip this log cycle
                        st.session_state["last_log_ts"] = now

            # ─── Troll / Nudge check — fires for ANY score < 90% ─────────────
            # Track how long the score has been below the "perfect" line
            now_ts = time.time()
            if score < 90:
                # Start timer if not already running
                if st.session_state.get('nudge_start_time') is None:
                    st.session_state['nudge_start_time'] = now_ts
                nudge_secs = now_ts - st.session_state['nudge_start_time']
            else:
                # Reset timer when focus is excellent
                st.session_state['nudge_start_time'] = None
                nudge_secs = 0.0

            if nudge_secs > 0:
                troll_result = check_and_trigger(
                    nudge_secs,
                    engagement_score=score,
                    sensitivity=st.session_state.get('nudge_sensitivity', 'Medium'),
                    troll_mode=st.session_state.get('troll_mode', True),
                    nudge_only=st.session_state.get('nudge_only', False),
                )
                if troll_result['should_trigger'] and troll_result['html']:
                    st.session_state['current_troll_html'] = troll_result['html']
                    st.session_state['troll_expire_at'] = now_ts + 15


            # High Visibility Warning for Low Engagement
            if score < 40:
                st.markdown("""
                <div style="background:rgba(255,82,82,0.15); border:2px solid #FF5252; 
                    border-radius:10px; padding:10px; text-align:center; margin-bottom:10px;
                    animation: blinker 1s linear infinite;">
                    <b style="color:#FF5252; font-size:1.1rem;">⚠️ LOW ENGAGEMENT DETECTED</b>
                </div>
                <style>
                    @keyframes blinker { 50% { opacity: 0.3; } }
                </style>
                """, unsafe_allow_html=True)

            # Camera condition warnings
            conditions = latest.get("conditions", {})
            if conditions and not conditions.get("ok", True):
                for warn in conditions.get("warnings", []):
                    st.warning(warn)

            # ─── Debug Mode Panel ─────────────────────────────────────
            if st.session_state.get("debug_mode", False):
                ear_val    = latest.get("ear", 0.0)
                yaw_val    = latest.get("yaw", 0.0)
                pitch_val  = latest.get("pitch", 0.0)
                gaze_val   = latest.get("gaze_score", 0.0)
                raw_s      = latest.get("raw_score", score)
                ema_s      = latest.get("ema_score", score)
                bonus      = latest.get("focus_bonus", 0)
                ear_clr    = "#00E676" if ear_val >= 0.28 else ("#FFD600" if ear_val >= 0.22 else "#FF5252")
                yaw_clr    = "#00E676" if abs(yaw_val)   <= 30 else "#FF5252"
                pitch_clr  = "#00E676" if -5 <= pitch_val <= 35 else "#FF5252"
                gaze_clr   = "#00E676" if gaze_val >= 0.7 else ("#FFD600" if gaze_val >= 0.4 else "#FF5252")
                score_clr  = "#00E676" if score >= 70 else ("#FFD600" if score >= 40 else "#FF5252")
                st.markdown(f"""
                <div style="background:rgba(0,0,0,0.4);border:1px solid #333;border-radius:10px;
                    padding:0.8rem;font-family:'JetBrains Mono',monospace;font-size:0.78rem;margin-top:0.5rem;">
                    <b style="color:#9E9E9E;">🛠️ DEBUG MODE — Raw CV Values</b><br>
                    <span style="color:{ear_clr};">EAR: {ear_val:.3f}</span> &nbsp;
                    <span style="color:{yaw_clr};">Yaw: {yaw_val:.1f}°</span> &nbsp;
                    <span style="color:{pitch_clr};">Pitch: {pitch_val:.1f}°</span> &nbsp;
                    <span style="color:{gaze_clr};">Gaze: {gaze_val:.3f}</span><br>
                    <span style="color:#9E9E9E;">Raw: {raw_s:.1f}%</span> &nbsp;
                    <span style="color:#9E9E9E;">EMA: {ema_s:.1f}%</span> &nbsp;
                    <span style="color:#FFD700;">Bonus: +{bonus}</span> &nbsp;
                    <span style="color:{score_clr};">Final: {score:.0f}%</span>
                </div>
                """, unsafe_allow_html=True)


        stats = st.session_state['live_stats']
        if stats['scores']:
            recent = stats['scores'][-15:]
            current_score = stats['scores'][-1]
            avg_score = sum(recent) / len(recent)

            score_color = "#00E676" if current_score >= 70 else ("#FFD600" if current_score >= 40 else "#FF5252")
            
            # --- Gamification Update ---
            if current_score >= 80:
                st.session_state['focus_streak'] = st.session_state.get('focus_streak', 0) + 1
                st.session_state['focus_points'] = st.session_state.get('focus_points', 0) + (10 if st.session_state['focus_streak'] > 10 else 5)
            else:
                st.session_state['focus_streak'] = 0

            # Mood & Streak Display
            mood_val = latest.get('sentiment', 'Neutral')
            mood_icon = "😊" if "Smiling" in mood_val else "😐" if "Focused" in mood_val else "😴" if "Sleepy" in mood_val else "🥱"
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05);padding:10px;border-radius:10px;text-align:center;border:1px solid rgba(255,255,255,0.1);">
                    <div style="font-size:0.75rem;color:#9E9E9E;">Current Mood</div>
                    <div style="font-size:1.1rem;font-weight:700;">{mood_icon} {mood_val}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                streak = st.session_state.get('focus_streak', 0)
                streak_clr = "#00E676" if streak > 20 else "#FFD700" if streak > 5 else "#9E9E9E"
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05);padding:10px;border-radius:10px;text-align:center;border:1px solid rgba(255,255,255,0.1);">
                    <div style="font-size:0.75rem;color:#9E9E9E;">Focus Streak</div>
                    <div style="font-size:1.1rem;font-weight:700;color:{streak_clr};">🔥 {streak}x</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="text-align:center;margin:1rem 0;">
                <div style="font-size:3.5rem;font-weight:900;color:{score_color};
                    text-shadow:0 0 20px {score_color}44;
                    font-family:'JetBrains Mono',monospace;">
                    {current_score:.0f}%
                </div>
                <div style="color:#9E9E9E;font-size:0.85rem;">Current Engagement</div>
            </div>
            """, unsafe_allow_html=True)


            m1, m2 = st.columns(2)
            with m1:
                render_metric_card("Avg (15s)", f"{avg_score:.0f}%", "📊")
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

        # Live Chart
        st.divider()
        st.subheader("📈 Engagement Timeline")
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
            fig.add_hline(y=focused_threshold, line_dash="dot", line_color="#00E676")
            fig.add_hline(y=distracted_threshold, line_dash="dot", line_color="#FF5252")
            fig.update_layout(
                yaxis=dict(range=[0, 105], gridcolor='rgba(255,255,255,0.05)'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(26,29,39,0.5)', height=280,
                margin=dict(l=0, r=0, t=20, b=0),
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # AI Insight button
            if st.button("🤖 AI Analysis (This Session)", use_container_width=True):
                from gemini_utils import generate_session_summary
                api_key = st.session_state.get("settings_config", {}).get("gemini_api_key", "")
                if api_key:
                    with st.spinner("AI analyzing your current session..."):
                        summary = generate_session_summary(api_key, {
                            "name": "Live Analysis", "avg_engagement": avg_score,
                            "peak_engagement": peak, "distractions": stats['distractions'],
                            "duration": (time.time() - st.session_state['session_start_ts']) / 60
                        })
                        st.markdown(f"""
                        <div class="glass-panel" style="margin-top:1rem;">
                            <h4>🤖 AI Couch Analysis</h4>
                            {summary}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("Please add a Gemini API key in Settings for AI analysis!")
        else:
            st.info("📊 Timeline will update once session data is recorded.")

    render_live_dashboard()

# ─── Global Troll Renderer ────────────────────────────────────────────────────
if st.session_state.get('current_troll_html'):
    if time.time() < st.session_state.get('troll_expire_at', 0):
        st.markdown(st.session_state['current_troll_html'], unsafe_allow_html=True)
    else:
        st.session_state['current_troll_html'] = None


# Footer or extra logic can go here
