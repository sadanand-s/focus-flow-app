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
from datetime import timezone

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
    preauthorized=config.get('pre-authorized', {}).get('emails', [])
)

# ─── Login Flow ──────────────────────────────────────────────────────────────

if not st.session_state.get('authentication_status'):

    # Read caught state from query params
    if st.query_params.get('caught') == 'true':
        st.session_state['troll_caught'] = True
        st.query_params.pop('caught', None)

    troll_enabled = st.session_state.get('troll_mode', True)
    troll_caught = st.session_state.get('troll_caught', False)

    if troll_enabled and not troll_caught:
        # ─── Troll Login Screen ───────────────────────────────────
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0 0.5rem 0;">
            <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">
                <span style="background: linear-gradient(135deg, #6C63FF, #00D2FF);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                🧠 Focus Flow</span>
            </h1>
            <p style="color: #9E9E9E; font-size: 1.1rem; margin-bottom: 0.3rem;">
                Student Engagement Monitoring System
            </p>
            <p style="color: #6C63FF; font-size: 1rem; font-weight: 600;">
                👆 Catch the bouncing button to unlock login!
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Inject postMessage listener so the iframe can signal when caught
        st.markdown("""
        <script>
        window.addEventListener('message', function(e) {
            if (e.data && e.data.type === 'troll_caught') {
                sessionStorage.setItem('st_troll_caught', 'true');
                const url = new URL(window.location.href);
                url.searchParams.set('caught', 'true');
                window.location.assign(url.toString());
            }
        });
        // Auto-skip logic
        (function() {
            if (sessionStorage.getItem('st_troll_caught') === 'true' || 
                sessionStorage.getItem('troll_done') === 'true') {
                const url = new URL(window.location.href);
                if (!url.searchParams.has('caught')) {
                    url.searchParams.set('caught', 'true');
                    window.location.assign(url.toString());
                }
            }
        })();
        </script>
        """, unsafe_allow_html=True)

        # Load troll button HTML
        troll_path = os.path.join(os.path.dirname(__file__), "ui_components", "troll_login.html")
        if os.path.exists(troll_path):
            with open(troll_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            components.html(html_content, height=420, scrolling=False)
        else:
            st.session_state['troll_caught'] = True
            st.rerun()

        # Fallback skip button
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🎯 I Caught It! (Skip)", use_container_width=True, key="troll_skip"):
                st.session_state['troll_caught'] = True
                st.rerun()

    else:
        # ─── Standard Login Form ──────────────────────────────────
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0 1rem 0;">
            <div id="app-logo" style="cursor: pointer; display: inline-block;"
                 onclick="handleLogoCick()">
                <h1 style="font-size: 2.8rem; margin-bottom: 0.5rem;">
                    <span style="background: linear-gradient(135deg, #6C63FF, #00D2FF);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    🧠 Focus Flow</span>
                </h1>
            </div>
            <p style="color: #9E9E9E; font-size: 1rem;">
                Login to start monitoring your study engagement
            </p>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.2/dist/confetti.browser.min.js"></script>
        <script>
        var _logoClicks = 0, _logoTimer = null;
        function handleLogoCick() {
            _logoClicks++;
            clearTimeout(_logoTimer);
            _logoTimer = setTimeout(function() { _logoClicks = 0; }, 1500);
            if (_logoClicks >= 5) {
                _logoClicks = 0;
                confetti({
                    particleCount: 150,
                    spread: 80,
                    origin: { y: 0.4 },
                    colors: ['#6C63FF', '#00D2FF', '#00E676', '#FFD600', '#FF5252']
                });
            }
        }
        </script>
        """, unsafe_allow_html=True)

        try:
            # In version 0.4.1+, location is mandatory
            authenticator.login(location='main')
        except Exception as e:
            st.error(f"Login error: {e}")

        if st.session_state.get('authentication_status') is False:
            st.error("❌ Username or password is incorrect.")
        elif st.session_state.get('authentication_status') is None:
            st.info("💡 Default credentials: **student** / **student123**")

            # Registration expander
            with st.expander("📝 Create New Account"):
                try:
                    pre_auth = config.get('pre-authorized', {})
                    if isinstance(pre_auth, dict):
                        emails = pre_auth.get('emails', [])
                    else:
                        emails = []
                    if authenticator.register_user(pre_authorized=emails):
                        st.success("✅ Account created! You can now login.")
                        with open(config_path, 'w') as f:
                            yaml.dump(config, f, default_flow_style=False)
                except Exception as e:
                    st.error(f"Registration error: {e}")


# ─── Authenticated Home ──────────────────────────────────────────────────────

if st.session_state.get('authentication_status'):
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
                Welcome, <b>{st.session_state.get('name', 'User')}</b>!
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
            <style>
            @keyframes pulse-dot {
                0%,100%{box-shadow:0 0 4px #00E676;}
                50%{box-shadow:0 0 14px #00E676;}
            }
            </style>
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
        authenticator.logout("🚪 Logout", "sidebar")

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

    # Save config if changed
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    except Exception:
        pass
