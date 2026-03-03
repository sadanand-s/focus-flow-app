"""
5_About.py — About page for Focus Flow.
"""
import streamlit as st
from utils import apply_theme, render_page_header

# ─── Page Setup ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="About — Focus Flow", page_icon="🧠", layout="wide")
apply_theme(st.session_state.get("theme", "Dark"))

app_name = st.session_state.get("app_name", "Focus Flow")

render_page_header("📖 About Focus Flow",
                   "The science and technology behind AI-powered focus monitoring.")

# ─── Hero ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align: center; padding: 3rem 1rem 2.5rem 1rem;
    background: linear-gradient(135deg, rgba(108,99,255,0.08), rgba(0,210,255,0.05));
    border: 1px solid rgba(108,99,255,0.2); border-radius: 16px; margin-bottom: 2rem;">
    <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">🧠</div>
    <h1 style="font-size: 3rem; margin: 0 0 0.3rem 0;
        background: linear-gradient(135deg, #6C63FF, #00D2FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;">{app_name}</h1>
    <p style="font-size: 1.15rem; color: #FFFFFF; font-weight: 300; margin: 0.5rem 0 1rem 0;">
        Student Engagement Monitoring System
    </p>
    <span style="background: rgba(0,230,118,0.12); color: #00E676;
        border: 1px solid rgba(0,230,118,0.3); border-radius: 20px;
        padding: 4px 14px; font-size: 0.8rem; font-weight: 600; letter-spacing: 1px;">
        v2.0 &nbsp;·&nbsp; Open Source &nbsp;·&nbsp; Student Project
    </span>
</div>
""", unsafe_allow_html=True)

# ─── Mission ──────────────────────────────────────────────────────────────────
mc1, mc2 = st.columns([2, 1])
with mc1:
    st.markdown(f"""
    ### 🌟 What is {app_name}?

    **{app_name}** is a first-year engineering student project that uses
    **computer vision + AI** to help you stay focused during study sessions.

    It watches you through your webcam (privately, locally — nothing leaves your machine),
    detects when you're getting distracted or drowsy, and gives you a fun nudge to
    get back on track. It also generates AI-powered session reports using **Google Gemini**.

    > *Built as a learning project — feedback and contributions welcome!*
    """)

with mc2:
    st.markdown("""
    <div style="background: rgba(108,99,255,0.08); border: 1px solid rgba(108,99,255,0.25);
        border-radius: 12px; padding: 1.2rem 1.5rem;">
        <p style="font-style: italic; color: #B0B8C8; margin: 0 0 0.8rem 0;">
            "Focus is the new IQ. In a noisy world,
             the ability to concentrate is a superpower."
        </p>
        <p style="text-align: right; font-weight: bold; color: #6C63FF; margin: 0;">
            — The Focus Flow Team
        </p>
    </div>
    """, unsafe_allow_html=True)

# ─── How It Works ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("🚀 How It Works")

h1, h2, h3 = st.columns(3)
card_style = """background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 1.5rem; min-height: 180px;"""

with h1:
    st.markdown(f"""
    <div style="{card_style}">
        <h4 style="margin:0 0 0.5rem 0;">📹 1. Frame Capture</h4>
        <p style="color:#9E9E9E; margin:0;">Your webcam frames are processed locally using OpenCV. No video ever leaves your device.</p>
    </div>
    """, unsafe_allow_html=True)

with h2:
    st.markdown(f"""
    <div style="{card_style}">
        <h4 style="margin:0 0 0.5rem 0;">🔬 2. AI Analysis</h4>
        <p style="color:#9E9E9E; margin:0;">MediaPipe FaceMesh tracks 468 face landmarks — eyes, head pose, gaze direction — all in real time.</p>
    </div>
    """, unsafe_allow_html=True)

with h3:
    st.markdown(f"""
    <div style="{card_style}">
        <h4 style="margin:0 0 0.5rem 0;">📊 3. Score & Nudge</h4>
        <p style="color:#9E9E9E; margin:0;">An ML classifier checks your engagement score every frame and triggers a fun troll nudge if you're drifting.</p>
    </div>
    """, unsafe_allow_html=True)

# ─── Engagement Indices ───────────────────────────────────────────────────────
st.divider()
st.subheader("📏 How Engagement is Measured")

idx_tab1, idx_tab2, idx_tab3 = st.tabs(["👁️ Eye Aspect Ratio", "🖥️ Gaze Direction", "👤 Head Pose"])

with idx_tab1:
    st.markdown("""
    **Eye Aspect Ratio (EAR)** measures the vertical vs horizontal distance between eyelids.
    - **Normal**: EAR ≈ 0.25–0.35 (regular blinking)
    - **Drowsy**: EAR < 0.25 sustained for 20+ frames
    """)
    st.code("EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)", language="text")

with idx_tab2:
    st.markdown("""
    **Gaze Direction** uses iris position relative to eye corners to estimate where you're looking.
    - **On-task**: Iris centered in eye (score ~1.0)
    - **Distracted**: Iris shifted to edge (score < 0.4)
    """)

with idx_tab3:
    st.markdown("""
    **Head Pose** uses solvePnP to compute yaw (left/right), pitch (up/down), and roll angles.
    - **Attentive**: Yaw < 30°, Pitch < 20°
    - **Distracted**: Looking sideways or down at phone
    """)

# ─── Tech Stack ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("🛠️ Tech Stack")

t1, t2 = st.columns(2)
with t1:
    st.markdown("""
| Layer | Technology |
|---|---|
| **UI** | Streamlit 1.42 |
| **CV Engine** | OpenCV + MediaPipe |
| **ML Model** | Scikit-Learn (RandomForest) |
| **AI Reports** | Google Gemini API |
    """)
with t2:
    st.markdown("""
| Layer | Technology |
|---|---|
| **Database** | SQLAlchemy + SQLite |
| **Exports** | FPDF2 + Pandas |
| **Auth** | Streamlit-Authenticator |
| **Camera** | streamlit-webrtc + aiortc |
    """)

# ─── Privacy ──────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔒 Privacy First")

p1, p2 = st.columns(2)
with p1:
    st.info("""
**Local-First Processing**

All computer vision runs 100% on your machine.
Only high-level numeric scores (engagement %, distraction count)
are saved to the local database. No video, no screenshots, nothing leaves your device.
    """)

with p2:
    st.success("""
**Open Source**

The full source code is available on GitHub. You can inspect,
modify, and host this yourself. No accounts, no subscriptions — just run it locally for free.
    """)

# ─── Credits ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center; padding: 2rem 0; color: #9E9E9E; font-size: 0.85rem;">
    <p style="margin:0;">🧠 <b>Focus Flow</b> &nbsp;·&nbsp; First Year Student Project &nbsp;·&nbsp; Open Source</p>
    <p style="margin:0.5rem 0 0 0;">Made with ❤️ using Python, Streamlit, MediaPipe &amp; Google Gemini</p>
</div>
""", unsafe_allow_html=True)
