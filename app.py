"""
app.py — Main entrypoint for Focus Flow.
Includes the 'Troll Button' unlock mechanic and direct app access (no login).
"""
import streamlit as st
import streamlit.components.v1 as components
import os
from utils import apply_theme, init_session_defaults, render_page_header, require_auth
from database import init_db

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Focus Flow — Student Engagement Monitor",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Initialize ──────────────────────────────────────────────────────────────
init_session_defaults()
# Bypass standard login pages
st.session_state["authentication_status"] = True
st.session_state["name"] = "Administrator"
st.session_state["username"] = "admin"

apply_theme(st.session_state.get("theme", "Dark"))

# Initialize database
try:
    init_db()
except Exception as e:
    st.error(f"Database initialization failed: {e}")




# ─── Troll Button Mechanic ────────────────────────────────────────────────────
if not st.session_state.get('troll_caught', False):
    st.markdown("""
    <div style="text-align: center; padding: 2rem 1rem 0 1rem;">
        <h1 style="font-size: 3.5rem; background: linear-gradient(135deg, #FF6B35, #FFD700);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
            👺 Troll Flow
        </h1>
        <p style="color: #9E9E9E; font-size: 1.1rem; margin: 0.5rem 0 2rem 0;">
            Catch the button to unlock your productivity!
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Troll animation + a hidden counter stored via a form ──────────────────
    # We use a Streamlit form with a checkbox trick to detect the click,
    # because iframe JS cannot reliably reach parent on Streamlit Cloud.
    
    troll_button_html = """
    <div id="troll-container" style="height: 400px; position: relative; border: 2px dashed rgba(255,107,53,0.3); border-radius: 20px; overflow: hidden; background: rgba(255,107,53,0.05); cursor: crosshair;">
        <button id="troll-btn" style="
            position: absolute;
            padding: 16px 32px;
            font-size: 1.1rem;
            font-weight: bold;
            color: white;
            background: linear-gradient(135deg, #FF6B35, #FFD700);
            border: none;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 8px 20px rgba(255,107,53,0.4);
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            transition: all 0.15s cubic-bezier(0.18, 0.89, 0.32, 1.28);
            white-space: nowrap;
            user-select: none;
        ">
            🚀 CLICK ME TO ENTER
        </button>
        <div id="caught-msg" style="display:none; text-align:center; padding-top:160px;">
            <div style="font-size:3rem;">🎉</div>
            <p style="color:#FFD700; font-size:1.3rem; font-weight:bold;">You caught it! Now click the button below!</p>
        </div>
    </div>

    <script>
        const btn = document.getElementById('troll-btn');
        const container = document.getElementById('troll-container');
        const caughtMsg = document.getElementById('caught-msg');
        let moveCount = 0;
        const maxMoves = 10;

        function moveButton() {
            if (moveCount < maxMoves) {
                const rect = container.getBoundingClientRect();
                const btnW = btn.offsetWidth;
                const btnH = btn.offsetHeight;
                const maxX = container.clientWidth  - btnW - 20;
                const maxY = container.clientHeight - btnH - 20;
                const newX = Math.max(10, Math.random() * maxX);
                const newY = Math.max(10, Math.random() * maxY);
                btn.style.left = newX + 'px';
                btn.style.top  = newY + 'px';
                btn.style.transform = 'none';
                btn.style.transitionDuration = Math.max(0.05, 0.18 - moveCount * 0.015) + 's';
                moveCount++;
            }
        }

        btn.addEventListener('mouseover', moveButton);
        btn.addEventListener('mousedown', moveButton);

        btn.addEventListener('click', function() {
            if (moveCount >= maxMoves) {
                // They caught it — hide the button, show success message
                btn.style.display = 'none';
                caughtMsg.style.display = 'block';
            } else {
                moveButton();
            }
        });
    </script>
    """

    components.html(troll_button_html, height=430)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Native Streamlit button — ALWAYS works on both localhost & cloud ───────
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        if st.button("✅ I Caught It — Enter Focus Flow!", type="primary", use_container_width=True):
            st.session_state.troll_caught = True
            st.switch_page("pages/0_Home.py")

    st.stop()


# ─── Authenticated Home (Bypassed but Troll-Locked) ───────────────────────────

require_auth()
apply_theme(st.session_state.get("theme", "Dark"))

# Sidebar
with st.sidebar:
    app_name = st.session_state.get("settings_config", {}).get("app_name", st.session_state.get("app_name", "Focus Flow"))
    session_active = bool(st.session_state.get('current_session_id'))

    st.markdown(f"""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="font-size: 2.5rem;">🧠</div>
        <h2 style="background: linear-gradient(135deg, #6C63FF, #00D2FF);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-size: 1.4rem; margin: 0.5rem 0 0.3rem 0;">{app_name}</h2>
        <p style="color: #9E9E9E; font-size: 0.85rem;">
            Welcome! Control your session from the dashboard.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Live session status dot
    if session_active:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;padding:4px 0;">
            <span style="display:inline-block;width:10px;height:10px;
                border-radius:50%;background:#00E676;
                box-shadow:0 0 8px #00E676;
                animation:pulse-dot 1.5s ease-in-out infinite;"></span>
            <span style="color:#00E676;font-size:0.85rem;font-weight:600;">Session Live</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;padding:4px 0;">
            <span style="display:inline-block;width:10px;height:10px;
                border-radius:50%;background:#555;"></span>
            <span style="color:#9E9E9E;font-size:0.85rem;">No active session</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    if st.button("🔄 Reset Troll App"):
        st.session_state.troll_caught = False
        st.query_params.clear()
        st.rerun()

# Main content — Home page
render_page_header("🏠 Welcome to Focus Flow", "Your AI-powered study engagement companion")

# Quick stats overview
col1, col2, col3, col4 = st.columns(4)
cards = [
    ("📹", "Live", "Dashboard", "Go to Dashboard to start your webcam session"),
    ("📊", "Track", "Analytics", "View your performance trends over time"),
    ("🤖", "AI", "Insights", "Get Gemini-powered coaching from your data"),
    ("🎯", "Focus", "Goals", "Set and track personal engagement targets"),
]
for col, (icon, val, label, tip) in zip([col1, col2, col3, col4], cards):
    with col:
        st.markdown(f"""
        <div class="metric-card" title="{tip}">
            <div style="font-size: 1.5rem;">{icon}</div>
            <div class="metric-value">{val}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Getting started guide
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("🚀 Quick Start Guide")
    st.markdown("""
    1. **Go to Dashboard** → Start a new study session with your webcam
    2. **Study!** → The system tracks your engagement in real-time
    3. **View Analytics** → Review your session performance and trends
    4. **Export Reports** → Download PDF/CSV reports of your sessions
    5. **Configure Settings** → Customize themes, nudges, and integrations
    """)

    if st.session_state.get('current_session_id'):
        st.info("📹 You have an active session! Head to the **Dashboard** to continue.")

with col_right:
    st.subheader("📌 Features")
    st.markdown("""
    - 👁️ **Eye Tracking** — EAR-based drowsiness detection
    - 🖥️ **Head Pose** — Gaze direction estimation
    - 🤡 **Troll Mode** — Fun nudges when distracted
    - 🤖 **AI Coach** — Gemini-powered insights
    - 📄 **Session Reports** — PDF & CSV exports
    - 🔒 **Anti-Spoofing** — Photo detection
    - 📈 **ML Training** — Personalized engagement model
    """)
