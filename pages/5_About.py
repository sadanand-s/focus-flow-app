"""
6_About.py — About page with app description, tech stack, credits, and version info.
"""
import streamlit as st
from utils import apply_theme, render_page_header

st.set_page_config(page_title="About — Focus Flow", page_icon="🧠", layout="wide")
apply_theme(st.session_state.get("theme", "Dark"))

render_page_header("ℹ️ About Focus Flow", "AI-powered student engagement monitoring")

# ─── App Description ─────────────────────────────────────────────────────────
st.markdown("""
<div style="background: linear-gradient(135deg, #1a1d26, #252838); border-radius: 16px;
    padding: 2rem; margin-bottom: 2rem; border: 1px solid #2D3348;">
    <h3 style="margin-top: 0;">🧠 What is Focus Flow?</h3>
    <p style="color: #B0B8C8; line-height: 1.7;">
        Focus Flow is an AI-powered study engagement monitoring system that uses your webcam to
        track your focus, attention, and alertness during study sessions. It combines computer vision,
        machine learning, and (optionally) Google's Gemini AI to provide real-time feedback, detailed
        analytics, and actionable insights to help you become a more effective learner.
    </p>
    <p style="color: #B0B8C8; line-height: 1.7;">
        Whether you're cramming for exams or doing a deep-focus coding session, Focus Flow keeps
        you accountable — with a sprinkle of humor through its troll/nudge system when you drift off! 🤡
    </p>
</div>
""", unsafe_allow_html=True)

# ─── How It Works ────────────────────────────────────────────────────────────
st.subheader("🔬 How It Works")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📹</div>
        <div style="font-weight: 700; color: #FF4B4B;">Step 1</div>
        <div class="metric-label">Capture</div>
        <p style="font-size: 0.8rem; color: #888; margin-top: 0.5rem;">
            Your webcam feeds live video to the CV engine
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</div>
        <div style="font-weight: 700; color: #FF4B4B;">Step 2</div>
        <div class="metric-label">Analyze</div>
        <p style="font-size: 0.8rem; color: #888; margin-top: 0.5rem;">
            MediaPipe detects face landmarks, eyes, iris, and head pose
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🧮</div>
        <div style="font-weight: 700; color: #FF4B4B;">Step 3</div>
        <div class="metric-label">Score</div>
        <p style="font-size: 0.8rem; color: #888; margin-top: 0.5rem;">
            Composite engagement score from gaze, pose, EAR, and expression
        </p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
        <div style="font-weight: 700; color: #FF4B4B;">Step 4</div>
        <div class="metric-label">Report</div>
        <p style="font-size: 0.8rem; color: #888; margin-top: 0.5rem;">
            Real-time dashboard, analytics, and exportable reports
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Engagement Score Breakdown ──────────────────────────────────────────────
with st.expander("📐 Engagement Score Formula"):
    st.markdown("""
    The composite engagement score is calculated as:

    ```
    engagement_score = (
        0.35 × gaze_score +
        0.25 × head_pose_score +
        0.20 × ear_score +
        0.10 × presence_score +
        0.10 × expression_score
    ) × 100
    ```

    | Component | Weight | Description |
    |-----------|--------|-------------|
    | **Gaze Score** | 35% | Iris position relative to eye corners (center = 1.0) |
    | **Head Pose** | 25% | Pitch/yaw deviation from forward-facing |
    | **EAR Score** | 20% | Eye Aspect Ratio — drowsiness detection |
    | **Presence** | 10% | Face detected in frame |
    | **Expression** | 10% | Facial expression analysis (yawning, etc.) |

    **Thresholds:**
    - EAR < 0.25 for 20+ frames → Drowsy
    - Yaw > 30° or Pitch > 20° → Looking away
    - No face for 3+ seconds → Away
    """)

# ─── Tech Stack ──────────────────────────────────────────────────────────────
st.subheader("🛠️ Tech Stack")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    | Technology | Purpose |
    |-----------|---------|
    | **Streamlit** | Web framework & UI |
    | **OpenCV** | Image processing |
    | **MediaPipe** | Face mesh & landmark detection |
    | **scikit-learn** | ML engagement model |
    | **Plotly** | Interactive charts |
    | **Altair** | Additional visualizations |
    """)

with col_b:
    st.markdown("""
    | Technology | Purpose |
    |-----------|---------|
    | **SQLAlchemy** | Database ORM |
    | **SQLite/PostgreSQL** | Data storage |
    | **Google Gemini** | AI-powered insights |
    | **FPDF2** | PDF report generation |
    | **streamlit-webrtc** | WebRTC webcam streaming |
    | **FastAPI** | Optional API sidecar |
    """)

st.divider()

# ─── Anti-Spoofing ───────────────────────────────────────────────────────────
with st.expander("🛡️ Anti-Spoofing System"):
    st.markdown("""
    Focus Flow includes a photo/spoof detection system:

    1. **Frame-to-frame variance analysis** — compares consecutive grayscale frames
    2. If the pixel variance remains below a threshold for ~5 seconds → flagged as static image
    3. A warning banner is displayed on the live feed
    4. The incident is logged in the session report

    This prevents users from propping up a photo of themselves instead of actually studying! 📸🚫
    """)

# ─── Credits ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("👨‍💻 Credits")

st.markdown("""
<div style="background: linear-gradient(135deg, #1a1d26, #252838); border-radius: 16px;
    padding: 1.5rem; border: 1px solid #2D3348; text-align: center;">
    <p style="color: #B0B8C8; margin-bottom: 0.5rem;">Built with ❤️ by</p>
    <h3 style="background: linear-gradient(135deg, #FF4B4B, #FF6B6B);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0;">SADA</h3>
    <p style="color: #888; font-size: 0.85rem; margin-top: 0.5rem;">
        Student Engagement Monitoring System
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_g1, col_g2, col_g3 = st.columns(3)
with col_g1:
    st.markdown("🔗 [GitHub Repository](https://github.com/your-username/focus-flow)")
with col_g2:
    st.markdown("📝 [Report a Bug](https://github.com/your-username/focus-flow/issues)")
with col_g3:
    st.markdown("💬 [Feedback](https://github.com/your-username/focus-flow/discussions)")

st.divider()

# Version
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8rem; padding: 1rem;">
    Focus Flow v1.0.0 | Powered by Streamlit & MediaPipe
</div>
""", unsafe_allow_html=True)
