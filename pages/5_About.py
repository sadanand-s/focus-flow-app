import streamlit as st
from utils import apply_theme, render_page_header, t

# ─── Page Setup ─────────────────────────────────────────────────────────────
app_name = st.session_state.settings_config.get("app_name", "Focus Flow")
st.set_page_config(page_title=f"{app_name} - About", page_icon="🧠", layout="wide")
apply_theme()

render_page_header(f"📖 {t('about')}", "The science and technology behind AI-powered focus.")

# ─── Hero Section ────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="glass-panel" style="text-align: center; padding: 4rem 1rem; border: 1px solid rgba(108, 99, 255, 0.3); border-radius: 24px;">
    <h1 style="font-size: 4rem; margin-bottom: 0.5rem; background: linear-gradient(135deg, #6C63FF, #00D2FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🧠 {app_name}</h1>
    <p style="font-size: 1.4rem; color: #FFFFFF; font-weight: 300;">Elevating Student Concentration with AI & Compassion</p>
    <div style="margin-top: 2rem;">
        <span class="status-dot status-live"></span> <span style="font-weight: 700; color: #00E676; letter-spacing: 1px;">V2.1.0 PREMIUM EDITION</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Mission Section ─────────────────────────────────────────────────────────
st.write("")
m_col1, m_col2 = st.columns([2, 1])
with m_col1:
    st.markdown(f"""
    ### 🌟 Our Mission
    In an era of endless digital noise, **{app_name}** was born from a simple observation: students aren't just losing focus—they're losing the *joy* of deep work. 
    
    We didn't build just another monitoring tool. We built a **Study Partner**. Our mission is to bridge the gap between human physiology and digital productivity. By using subtle, non-intrusive AI triggers, we help you stay in the 'Flow State' longer, while ensuring your data remains yours and yours alone.
    """)
with m_col2:
    st.markdown(f"""
    <div class="glass-panel" style="background: rgba(108, 99, 255, 0.1); border-color: rgba(108, 99, 255, 0.4);">
        <p style="font-style: italic; color: #B0B8C8;">"Focus is the new IQ. In a noisy world, the ability to concentrate is a superpower."</p>
        <p style="text-align: right; font-weight: bold; color: #6C63FF;">— The {app_name} Team</p>
    </div>
    """, unsafe_allow_html=True)

# ─── How it Works ────────────────────────────────────────────────────────────
st.divider()
st.subheader("🚀 How It Works")
h1, h2, h3 = st.columns(3)
with h1:
    st.markdown("""
    <div class="glass-panel" style="height: 250px;">
        <h3>📹 1. Frame Capture</h3>
        <p>Your webcam captures video frames which are processed locally using OpenCV. No raw video ever leaves your device.</p>
    </div>
    """, unsafe_allow_html=True)
with h2:
    st.markdown("""
    <div class="glass-panel" style="height: 250px;">
        <h3>🔬 2. AI Analysis</h3>
        <p>MediaPipe FaceMesh detects 468 points on your face, tracking eye blinks (EAR), gaze vector, and head orientation.</p>
    </div>
    """, unsafe_allow_html=True)
with h3:
    st.markdown("""
    <div class="glass-panel" style="height: 250px;">
        <h3>📊 3. Focus Scoring</h3>
        <p>A RandomForest classifier processes these features to calculate your focus percentage and triggers nudges if you drift.</p>
    </div>
    """, unsafe_allow_html=True)

# ─── The Indices ────────────────────────────────────────────────────────────
st.divider()
st.subheader("📏 Engagement Indices")
idx_tab1, idx_tab2, idx_tab3, idx_tab4 = st.tabs(["👁️ EAR", "🖥️ Gaze", "👤 Posture", "🧠 Expression"])

with idx_tab1:
    st.markdown("""
    **Eye Aspect Ratio (EAR)**: Measures the distance between eyelids. 
    - **Focused**: Stable, regular blinking.
    - **Drowsy**: Prolonged eye closure (low EAR).
    - **Distracted**: Eyes repeatedly moving away from center.
    """)
    st.code("EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)")

with idx_tab2:
    st.markdown("""
    **Gaze Direction**: Calculates the vector between the eye iris and the pupil center.
    - **Task-Aligned**: Vector points within 10 degrees of the webcam plane.
    - **Off-Task**: Looking at surroundings or phone.
    """)

with idx_tab3:
    st.markdown("""
    **Posture (Yaw/Pitch/Roll)**: Head pose estimation.
    - **Attentive**: Forward-facing, stable pitch.
    - **Bored**: Slouching or resting chin (high pitch/roll).
    """)

with idx_tab4:
    st.markdown("""
    **Micro-Expressions**: Analyzes eyebrow and mouth movement frequency. 
    - **Micro-shifts**: Frequent fidgeting or facial movement often correlates with decreasing focus.
    """)

# ─── Tech Stack ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("🛠️ The Tech Stack")
t1, t2 = st.columns(2)
with t1:
    st.markdown("""
    | Component | Tech Used |
    |---|---|
    | **Frontend** | Streamlit |
    | **CV Engine** | OpenCV + MediaPipe |
    | **ML Model** | Scikit-Learn (RandomForest) |
    | **Report AI** | Google Gemini API |
    """)
with t2:
    st.markdown("""
    | Component | Tech Used |
    |---|---|
    | **Database** | SQLAlchemy + SQLite/PostgreSQL |
    | **Exports** | FPDF2 + Pandas |
    | **Auth** | Streamlit-Authenticator |
    | **Deployment** | Docker + Streamlit Cloud |
    """)

# ─── Privacy & Performance ─────────────────────────────────────────────────
st.divider()
st.subheader("🔒 Privacy & Performance")
p1, p2 = st.columns(2)
with p1:
    st.write("### Local-First Architecture")
    st.write("We prioritize your privacy. All computer vision processing happens **on your machine**. Only high-level engagement scores are synced to your account database.")

with p2:
    st.write("### Optimizations")
    st.write("Using `st.cache_resource` and frame-skipping optimizations (15fps) to ensure smooth operation even on low-power student laptops.")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"""
<div style="text-align: center; opacity: 0.7; padding: 2rem 0;">
    <p>© 2026 {app_name} Open Source Project</p>
    <p>Made with ❤️ by the Google Advanced Agentic Coding Team</p>
    <a href="https://github.com/example/focus-flow" target="_blank">Star on GitHub ⭐</a> | 
    <a href="mailto:support@focusflow.app">Contact Us</a>
</div>
""", unsafe_allow_html=True)
