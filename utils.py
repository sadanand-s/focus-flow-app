"""
utils.py — Premium Shared utilities for the Focus Flow System.
Includes visual design system, multi-language support, and OBS overlay helpers.
"""
import streamlit as st
import numpy as np
import random
import time
from datetime import datetime, timedelta

def get_custom_css():
    settings = st.session_state.get('settings_config', {})
    accent = settings.get('accent_color', '#6C63FF')
    
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono&display=swap');
    :root {{
        --bg-color: #0F1117;
        --surface-color: #1A1D27;
        --accent-primary: {accent};
        --accent-secondary: #00D2FF;
        --success: #00E676;
        --warning: #FFD600;
        --error: #FF5252;
        --text-primary: #FFFFFF;
        --text-secondary: #9E9E9E;
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.08);
        --radius: 12px;
    }}
    .stApp {{ animation: fadeIn 0.6s ease-in-out; background-color: var(--bg-color); }}
    @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    
    .glass-panel {{
        background: var(--glass-bg); backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border); border-radius: var(--radius);
        padding: 20px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }}
    
    .metric-card {{
        background: var(--surface-color); border-radius: var(--radius);
        padding: 1.5rem; border: 1px solid var(--glass-border);
        transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        text-align: center; position: relative;
    }}
    .metric-card:hover {{ transform: translateY(-8px); border-color: var(--accent-primary); }}
    .metric-value {{ font-size: 2.2rem; font-weight: 800; font-family: 'JetBrains Mono'; }}
    .metric-label {{ color: var(--text-secondary); font-size: 0.8rem; font-weight: 700; letter-spacing: 1px; }}

    .stButton > button {{
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
        border-radius: 50px !important; color: white !important; font-weight: 700 !important;
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.3) !important;
    }}
    
    .status-dot {{ height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }}
    .status-live {{ background-color: var(--success); box-shadow: 0 0 12px var(--success); animation: pulseStatus 2s infinite; }}
    .status-idle {{ background-color: var(--text-secondary); }}
    @keyframes pulseStatus {{ 0% {{ transform: scale(0.95); opacity: 0.7; }} 70% {{ transform: scale(1.1); opacity: 1; }} 100% {{ transform: scale(0.95); opacity: 0.7; }} }}

    /* Overlay Mode Styles */
    .overlay-hud {{ position: fixed; top: 20px; right: 20px; z-index: 9999; pointer-events: none; }}
    .hud-card {{ background: rgba(0,0,0,0.7); padding: 10px 20px; border-radius: 12px; border: 1px solid var(--accent-primary); }}
    </style>
    """
    return css

LANGUAGES = {
    'English': {
        'welcome': 'Welcome', 'dashboard': 'Dashboard', 'sessions': 'Sessions', 'analytics': 'Analytics',
        'settings': 'Settings', 'about': 'About', 'integrations': 'Integrations', 'start_session': 'Start Session',
        'end_session': 'End Session', 'live_metric': 'Engagement', 'ear': 'Alertness', 'spoof_warn': '🚨 Activity detected!',
        'coach': 'AI Coach', 'streak': 'Streak'
    },
    'Spanish': {
        'welcome': 'Bienvenido', 'dashboard': 'Panel', 'sessions': 'Sesiones', 'analytics': 'Analítica',
        'settings': 'Ajustes', 'about': 'Acerca de', 'integrations': 'Integraciones', 'start_session': 'Comenzar',
        'end_session': 'Terminar', 'live_metric': 'Compromiso', 'ear': 'Alerta', 'spoof_warn': '🚨 Actividad detectada!',
        'coach': 'Coach AI', 'streak': 'Racha'
    }
}

def t(key):
    lang = st.session_state.settings_config.get('language', 'English')
    return LANGUAGES.get(lang, LANGUAGES['English']).get(key, key)

def apply_theme():
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    if st.query_params.get("overlay") == "true":
        st.markdown("<style>#MainMenu, footer, header, [data-testid='stSidebar'] {display: none !important;}</style>", unsafe_allow_html=True)

def require_auth():
    if not st.session_state.get("authentication_status"):
        st.warning("🔒 Please login from the main page.")
        st.stop()

def get_current_user_id(db):
    from database import User
    username = st.session_state.get("username", "student")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username, email=f"{username}@focusflow.app")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user.id

def format_duration(s):
    if not s: return "0s"
    m, s = divmod(int(s), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s" if h else f"{m}m {s}s" if m else f"{s}s"

def render_metric_card(label, value, icon="📊", tooltip=""):
    st.markdown(f'<div class="metric-card" title="{tooltip}"><div style="font-size: 1.5rem;">{icon}</div><div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

def render_page_header(title, subtitle="", status="idle"):
    dot = "status-live" if status == "live" else "status-idle"
    st.markdown(f"""
    <div class="glass-panel" id="header-container">
        <h1 style="margin:0; cursor:pointer;" onclick="triggerConfetti()"><span class="status-dot {dot}"></span>{title}</h1>
        <p style="opacity:0.8; margin-top:5px;">{subtitle}</p>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <script>
        let logoClicks = 0, lastLogoClick = 0;
        function triggerConfetti() {{
            const now = Date.now();
            if (now - lastLogoClick < 600) logoClicks++; else logoClicks = 1;
            lastLogoClick = now;
            if (logoClicks >= 5) {{
                confetti({{ particleCount: 150, spread: 70, origin: {{ y: 0.6 }} }});
                logoClicks = 0;
            }}
        }}
    </script>
    """, unsafe_allow_html=True)

def init_session_defaults():
    if "settings_config" not in st.session_state:
        st.session_state.settings_config = {
            "app_name": "Focus Flow", "accent_color": "#6C63FF", "language": "English", "focused_threshold": 70, 
            "distracted_threshold": 40, "ambient_sound": "None", "ambient_volume": 50, "widgets": {"engagement": True, "ear": True, "posture": True, "timeline": True}
        }
    defaults = {
        "authentication_status": None, "username": None, "troll_mode": True, "nudge_only": False, "streak_count": 0, "chat_history": [],
        "current_session_id": None, "live_stats": {"scores": [], "timestamps": [], "distractions": 0, "gaze_scores": [], "ear_values": []}
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v
