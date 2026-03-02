"""
app.py — Main entrypoint for Focus Flow Student Engagement Monitoring System.
Handles authentication, troll login mechanic, and session state initialization.
"""
import streamlit as st
import streamlit_authenticator as stauth
import streamlit.components.v1 as components
import yaml
from yaml.loader import SafeLoader
import os

from utils import apply_theme, init_session_defaults, render_page_header
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
apply_theme(st.session_state.get("theme", "Dark"))

# Initialize database
try:
    init_db()
except Exception as e:
    st.error(f"Database initialization failed: {e}")

# ─── Authentication Setup ────────────────────────────────────────────────────
config_path = os.path.join(os.path.dirname(__file__), "auth_config.yaml")

if not os.path.exists(config_path):
    st.error("⚠️ Authentication config file not found. Please ensure `auth_config.yaml` exists.")
    st.stop()

with open(config_path) as f:
    config = yaml.load(f, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

# ─── Login Flow ──────────────────────────────────────────────────────────────

if not st.session_state.get('authentication_status'):
    # Check query params for troll catch
    params = st.query_params
    if params.get("caught") == "true":
        st.session_state['troll_caught'] = True
        st.query_params.clear()

    troll_enabled = st.session_state.get('troll_mode', True)

    if troll_enabled and not st.session_state.get('troll_caught', False):
        # ─── Troll Login Screen ───────────────────────────────────
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0 0.5rem 0;">
            <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">
                <span style="background: linear-gradient(135deg, #FF4B4B, #FF6B6B);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                🧠 Focus Flow</span>
            </h1>
            <p style="color: #B0B8C8; font-size: 1.1rem; margin-bottom: 0.3rem;">
                Student Engagement Monitoring System
            </p>
            <p style="color: #FF6B6B; font-size: 1rem; font-weight: 600;
                animation: pulse 2s infinite;">
                👆 Catch the bouncing button to unlock login!
            </p>
            <style>
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            </style>
        </div>
        """, unsafe_allow_html=True)

        # Load troll button HTML
        troll_path = os.path.join(os.path.dirname(__file__), "ui_components", "troll_login.html")
        if os.path.exists(troll_path):
            with open(troll_path, "r") as f:
                html_content = f.read()
            components.html(html_content, height=380, scrolling=False)
        else:
            st.session_state['troll_caught'] = True
            st.rerun()

        # Skip button (backup)
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🎯 I Caught It!", use_container_width=True):
                st.session_state['troll_caught'] = True
                st.rerun()

    else:
        # ─── Standard Login Form ──────────────────────────────────
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0 1rem 0;">
            <h1 style="font-size: 2.8rem; margin-bottom: 0.5rem;">
                <span style="background: linear-gradient(135deg, #FF4B4B, #FF6B6B);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                🧠 Focus Flow</span>
            </h1>
            <p style="color: #B0B8C8; font-size: 1rem;">
                Login to start monitoring your study engagement
            </p>
        </div>
        """, unsafe_allow_html=True)

        try:
            authenticator.login()
        except Exception as e:
            st.error(f"Login error: {e}")

        if st.session_state.get('authentication_status') is False:
            st.error("❌ Username or password is incorrect.")
        elif st.session_state.get('authentication_status') is None:
            st.info("💡 Default credentials: **student** / **student123**")

            # Registration expander
            with st.expander("📝 Create New Account"):
                try:
                    if authenticator.register_user(pre_authorized=config.get('pre-authorized', {}).get('emails', [])):
                        st.success("✅ Account created! You can now login.")
                        with open(config_path, 'w') as f:
                            yaml.dump(config, f, default_flow_style=False)
                except Exception as e:
                    st.error(f"Registration error: {e}")


# ─── Authenticated Home ──────────────────────────────────────────────────────

if st.session_state.get('authentication_status'):
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 2.5rem;">🧠</div>
            <h2 style="background: linear-gradient(135deg, #FF4B4B, #FF6B6B);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                font-size: 1.4rem; margin: 0.5rem 0 0.3rem 0;">Focus Flow</h2>
            <p style="color: #B0B8C8; font-size: 0.85rem;">
                Welcome, <b>{st.session_state.get('name', 'User')}</b>!
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Session status indicator
        if st.session_state.get('current_session_id'):
            st.success("🟢 Session Active")
        else:
            st.caption("⚪ No active session")

        st.divider()
        authenticator.logout("🚪 Logout", "sidebar")

    # Main content — Home page
    render_page_header("🏠 Welcome to Focus Flow", "Your AI-powered study engagement companion")

    # Quick stats overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 1.5rem;">📹</div>
            <div class="metric-value">Live</div>
            <div class="metric-label">Dashboard</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 1.5rem;">📊</div>
            <div class="metric-value">Track</div>
            <div class="metric-label">Analytics</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 1.5rem;">🤖</div>
            <div class="metric-value">AI</div>
            <div class="metric-label">Insights</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 1.5rem;">🎯</div>
            <div class="metric-value">Focus</div>
            <div class="metric-label">Goals</div>
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

    # Save config if changed
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    except Exception:
        pass
