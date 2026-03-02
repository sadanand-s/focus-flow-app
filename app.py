import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
import streamlit.components.v1 as components

from utils import apply_theme, init_session_defaults, render_page_header, t
from database import init_db

# ─── Page Configuration ──────────────────────────────────────────────────────
init_session_defaults()
app_name = st.session_state.settings_config.get("app_name", "Focus Flow")

st.set_page_config(
    page_title=app_name,
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Premium Design System
apply_theme()

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
    config['cookie']['expiry_days']
)

# ─── Troll Login Overlay ───────────────────────────────────────────────────
def render_troll_overlay():
    troll_html = """
    <div id="troll-overlay">
        <button id="bouncy-btn" onclick="trollClicked()">🎯 CLICK ME</button>
    </div>
    <style>
        #troll-overlay {
            position: fixed; top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: #0F1117; z-index: 99999;
            overflow: hidden;
            display: flex; justify-content: center; align-items: center;
        }
        #bouncy-btn {
            position: absolute;
            padding: 18px 42px;
            font-size: 20px; font-weight: 800;
            background: linear-gradient(135deg, #6C63FF, #00D2FF);
            border: none; border-radius: 50px;
            color: white; cursor: pointer;
            box-shadow: 0 0 40px rgba(108,99,255,0.7);
            transition: transform 0.1s;
            user-select: none;
            z-index: 100000;
            font-family: 'Inter', sans-serif;
        }
        #bouncy-btn:hover { transform: scale(1.1); }
        #troll-overlay.hiding {
            animation: overlayFade 0.6s ease forwards;
        }
        @keyframes overlayFade {
            to { opacity: 0; pointer-events: none; }
        }
    </style>
    <script>
        if (sessionStorage.getItem('troll_done') === 'true') {
            document.getElementById('troll-overlay').remove();
        } else {
            let x = window.innerWidth / 2;
            let y = window.innerHeight / 2;
            let vx = 3.8, vy = 3.0;
            const btn = document.getElementById('bouncy-btn');
            btn.style.left = x + 'px';
            btn.style.top  = y + 'px';
            let animating = true;

            function bounce() {
                if (!animating) return;
                const W = window.innerWidth;
                const H = window.innerHeight;
                const bw = btn.offsetWidth || 160;
                const bh = btn.offsetHeight || 56;
                x += vx; y += vy;
                if (x <= 0) { x = 0; vx = Math.abs(vx); }
                if (x >= W - bw) { x = W - bw; vx = -Math.abs(vx); }
                if (y <= 0) { y = 0; vy = Math.abs(vy); }
                if (y >= H - bh) { y = H - bh; vy = -Math.abs(vy); }
                btn.style.left = x + 'px';
                btn.style.top  = y + 'px';
                requestAnimationFrame(bounce);
            }
            bounce();

            window.trollClicked = function() {
                animating = false;
                btn.textContent = '✅ Nice catch!';
                btn.style.transform = 'scale(1.3)';
                btn.style.background = '#00E676';
                setTimeout(() => {
                    document.getElementById('troll-overlay').classList.add('hiding');
                    setTimeout(() => {
                        document.getElementById('troll-overlay').remove();
                        sessionStorage.setItem('troll_done', 'true');
                    }, 600);
                }, 400);
            };
        }
    </script>
    """
    st.components.v1.html(troll_html, height=1, width=1)

if not st.session_state.get('authentication_status'):
    render_troll_overlay()
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write("")
        st.write("")
        # Easter Egg Logo
        st.markdown(f"""
            <div style="text-align: center; cursor: pointer; user-select: none;" id="logo-trigger">
                <span style="font-size: 5rem;">🧠</span>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
            <script>
                (function() {{
                    let clicks = 0;
                    let lastClick = 0;
                    const trigger = document.getElementById('logo-trigger');
                    if (trigger) {{
                        trigger.onclick = function() {{
                            const now = Date.now();
                            if (now - lastClick < 600) clicks++;
                            else clicks = 1;
                            lastClick = now;
                            if (clicks >= 5) {{
                                confetti({{
                                    particleCount: 150,
                                    spread: 70,
                                    origin: {{ y: 0.6 }},
                                    colors: ['#6C63FF', '#00D2FF', '#00E676']
                                }});
                                clicks = 0;
                            }}
                        }};
                    }}
                }})();
            </script>
        """, unsafe_allow_html=True)
        
        render_page_header(app_name, "Track. Analyze. Focus.")
        
        name, authentication_status, username = authenticator.login('main')
        
        if authentication_status == False:
            st.error('Username/password is incorrect')
        elif authentication_status == None:
            st.info('Please catch the button above to unlock the app!')

# ─── Logged In Content ──────────────────────────────────────────────────────
if st.session_state.get("authentication_status"):
    with st.sidebar:
        st.image(f"https://api.dicebear.com/7.x/bottts/svg?seed={st.session_state['username']}", width=100)
        st.write(f"### {t('welcome')}, {st.session_state['name']}!")
        authenticator.logout('Logout', 'sidebar')
        st.divider()
        st.write(f"🔥 **{t('streak')}:** {st.session_state.streak_count} days")
        
    render_page_header(f"{app_name} Home", "Your personal AI study companion.")

    # Main Grid
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="glass-panel">
            <h3>📹 {t('dashboard')}</h3>
            <p>Ready to start studying? Open the dashboard to begin real-time engagement tracking.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Start Live Dashboard", use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")

    with c2:
        st.markdown(f"""
        <div class="glass-panel">
            <h3>📈 {t('analytics')}</h3>
            <p>Check your deep focus trends, heatmaps, and AI-generated progress reports.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📈 View Performance", use_container_width=True):
            st.switch_page("pages/3_Analytics.py")

    st.divider()
    
    # Feature Overview
    feat1, feat2, feat3 = st.columns(3)
    with feat1:
        st.markdown("### 👁️ Precise Tracking\nTrack Attention, EAR, Gaze, and Posture with AI.")
    with feat2:
        st.markdown(f"### 🤖 {t('coach')}\nGet personalized study tips from Google's latest model.")
    with feat3:
        st.markdown("### 🤡 Smart Nudges\nConfigure fun trolls or subtle toasts to stay on track.")

    # Ambient sound player (bottom-left floating)
    config_settings = st.session_state.settings_config
    ambient = config_settings.get("ambient_sound", "None")
    if ambient != "None":
        sounds = {
            "Lo-fi": "jfKfPfyJRdk",
            "Rain": "mPZkdNFkNps",
            "White Noise": "nMfPqeZjc2c",
            "Forest": "M0wO7qc07e0"
        }
        vid_id = sounds.get(ambient, "jfKfPfyJRdk")
        st.markdown(f"""
            <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000; background: rgba(0,0,0,0.85); padding: 12px 24px; border-radius: 50px; border: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                <iframe width="0" height="0" src="https://www.youtube.com/embed/{vid_id}?autoplay=1&loop=1&playlist={vid_id}" frameborder="0"></iframe>
                <span style="color: white; font-size: 0.85rem; font-weight: 700;">🎵 {ambient} Mode</span>
            </div>
        """, unsafe_allow_html=True)
