"""
utils.py — Shared utilities for the Focus Flow Student Engagement System.
Modified to bypass authentication as per user request.
"""
import streamlit as st
import numpy as np
import random
from datetime import datetime, timedelta


# ─── Google Fonts (injected via <link> tag — more reliable than @import) ──────

_FONTS_INJECTED = False

def _inject_fonts():
    """Inject Google Fonts link tags once per page load."""
    global _FONTS_INJECTED
    if not _FONTS_INJECTED:
        st.markdown("""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)
        _FONTS_INJECTED = True


# ─── Theme CSS ────────────────────────────────────────────────────────────────

THEMES = {
    "Dark": """
    <style>
        :root {
            --bg-primary:    #0F1117;
            --bg-surface:    #1A1D27;
            --bg-card:       #1E2130;
            --accent:        #6C63FF;
            --accent2:       #00D2FF;
            --grad:          linear-gradient(135deg, #6C63FF, #00D2FF);
            --success:       #00E676;
            --warning:       #FFD600;
            --error:         #FF5252;
            --text:          #FFFFFF;
            --text-muted:    #9E9E9E;
            --border:        rgba(255,255,255,0.08);
        }

        /* Base */
        html, body, .stApp {
            background-color: var(--bg-primary) !important;
            font-family: 'Inter', 'Segoe UI', sans-serif !important;
            color: var(--text) !important;
        }

        /* Smooth page fade-in */
        .main .block-container {
            animation: fadein 0.4s ease;
        }
        @keyframes fadein {
            from { opacity: 0; transform: translateY(6px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* ─── Metric cards ──────────────────────────────── */
        .metric-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 1.2rem 0.8rem;
            text-align: center;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-3px);
            border-color: rgba(108,99,255,0.35);
        }
        .metric-card .metric-value {
            font-size: 1.8rem;
            font-weight: 800;
            background: var(--grad);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-family: 'JetBrains Mono', 'Courier New', monospace;
            line-height: 1.2;
        }
        .metric-card .metric-label {
            font-size: 0.72rem;
            color: var(--text-muted);
            margin-top: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }
        .metric-card .metric-icon {
            font-size: 1.3rem;
            margin-bottom: 0.2rem;
        }

        /* ─── Page header banner ────────────────────────── */
        .page-header {
            background: linear-gradient(135deg,
                rgba(108,99,255,0.1) 0%,
                rgba(0,210,255,0.06) 100%);
            border: 1px solid rgba(108,99,255,0.18);
            border-radius: 14px;
            padding: 1.5rem 1.8rem;
            margin-bottom: 1.8rem;
        }
        .page-header h1 {
            background: var(--grad);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2rem;
            font-weight: 800;
            margin: 0 0 0.2rem 0;
            line-height: 1.2;
        }
        .page-header p {
            color: var(--text-muted);
            margin: 0;
            font-size: 0.9rem;
        }

        /* ─── Sidebar ───────────────────────────────────── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0F1117 0%, #14172A 100%);
            border-right: 1px solid rgba(108,99,255,0.12);
        }

        /* ─── Buttons (gradient pill) ────────────────────── */
        .stButton > button {
            background: linear-gradient(135deg, #6C63FF, #00D2FF) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            padding: 0.45rem 1.2rem !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
            box-shadow: 0 3px 12px rgba(108,99,255,0.25) !important;
        }
        .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px rgba(108,99,255,0.4) !important;
        }
        .stButton > button:active {
            transform: translateY(0) !important;
        }
        /* Secondary / outline buttons */
        .stButton > button[kind="secondary"],
        .stButton > button[data-testid*="secondary"] {
            background: rgba(255,255,255,0.05) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            box-shadow: none !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background: rgba(255,255,255,0.1) !important;
            box-shadow: none !important;
        }

        /* ─── Inputs ────────────────────────────────────── */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 8px !important;
            color: white !important;
            font-family: 'Inter', sans-serif !important;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: rgba(108,99,255,0.5) !important;
            box-shadow: 0 0 0 2px rgba(108,99,255,0.12) !important;
        }
        .stSelectbox > div > div {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 8px !important;
        }

        /* ─── Tabs ──────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            padding: 3px;
            gap: 2px;
            border: 1px solid rgba(255,255,255,0.06);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 7px !important;
            color: var(--text-muted) !important;
            font-weight: 500 !important;
            font-family: 'Inter', sans-serif !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg,
                rgba(108,99,255,0.28), rgba(0,210,255,0.18)) !important;
            color: white !important;
        }

        /* ─── st.metric widget ──────────────────────────── */
        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 10px;
            padding: 0.7rem 1rem;
        }
        [data-testid="stMetricValue"] {
            font-family: 'JetBrains Mono', monospace !important;
        }

        /* ─── Glass panel (legacy class but restored for pages) ─── */
        .glass-panel {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            margin-bottom: 1rem !important;
            backdrop-filter: blur(8px);
        }

        /* ─── Code / pre ────────────────────────────────── */
        .stCodeBlock { border-radius: 8px !important; }
        pre {
            background: rgba(0,0,0,0.3) !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
        }

        /* ─── Alert boxes ───────────────────────────────── */
        .stAlert { border-radius: 8px !important; }

        /* ─── Divider ───────────────────────────────────── */
        hr { border-color: rgba(255,255,255,0.07) !important; }

        /* ─── Expander ──────────────────────────────────── */
        details[data-testid="stExpander"] > summary {
            border-radius: 8px !important;
        }

        /* ─── Thin scrollbar ────────────────────────────── */
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: rgba(108,99,255,0.3);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(108,99,255,0.55);
        }
    </style>
    """,

    "Light": """
    <style>
        :root {
            --bg-primary:  #F5F7FF;
            --bg-surface:  #FFFFFF;
            --bg-card:     #FFFFFF;
            --accent:      #6C63FF;
            --accent2:     #00A8CC;
            --grad:        linear-gradient(135deg, #6C63FF, #00A8CC);
            --success:     #00C853;
            --warning:     #FF9800;
            --error:       #F44336;
            --text:        #1A1A2E;
            --text-muted:  #666680;
            --border:      rgba(0,0,0,0.08);
        }
        html, body, .stApp {
            background-color: var(--bg-primary) !important;
            font-family: 'Inter', 'Segoe UI', sans-serif !important;
        }
        .main .block-container { animation: fadein 0.4s ease; }
        @keyframes fadein { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:none} }
        .metric-card {
            background: white; border: 1px solid rgba(0,0,0,0.07);
            border-radius: 12px; padding: 1.2rem 0.8rem; text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        .metric-card:hover { transform: translateY(-3px); }
        .metric-card .metric-value {
            font-size: 1.8rem; font-weight: 800;
            background: var(--grad); -webkit-background-clip: text;
            -webkit-text-fill-color: transparent; background-clip: text;
            font-family: 'JetBrains Mono', monospace;
        }
        .metric-card .metric-label { font-size:0.72rem; color:var(--text-muted); margin-top:0.3rem; text-transform:uppercase; letter-spacing:1px; }
        .page-header {
            background: linear-gradient(135deg,#EEEAFF,#E0F8FF);
            border: 1px solid rgba(108,99,255,0.15); border-radius: 14px;
            padding: 1.5rem 1.8rem; margin-bottom: 1.8rem;
        }
        .page-header h1 { background:var(--grad); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; font-size:2rem; font-weight:800; margin:0; }
        .page-header p { color:var(--text-muted); margin:0.3rem 0 0 0; font-size:0.9rem; }
        .stButton > button { background:var(--grad) !important; color:white !important; border:none !important; border-radius:8px !important; font-weight:600 !important; }
        section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid rgba(0,0,0,0.08); }
    </style>
    """,

    "Solarized": """
    <style>
        :root {
            --bg-primary:  #002B36;
            --bg-surface:  #073642;
            --bg-card:     #07404D;
            --accent:      #268BD2;
            --accent2:     #2AA198;
            --grad:        linear-gradient(135deg, #268BD2, #2AA198);
            --success:     #859900;
            --warning:     #B58900;
            --error:       #DC322F;
            --text:        #FDF6E3;
            --text-muted:  #93A1A1;
            --border:      rgba(101,123,131,0.35);
        }
        html, body, .stApp { background-color:var(--bg-primary) !important; font-family:'Inter','Segoe UI',sans-serif !important; }
        .main .block-container { animation: fadein 0.4s ease; }
        @keyframes fadein { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:none} }
        .metric-card { background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:1.2rem 0.8rem; text-align:center; transition:transform 0.2s; }
        .metric-card:hover { transform:translateY(-3px); }
        .metric-card .metric-value { font-size:1.8rem; font-weight:800; background:var(--grad); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; font-family:'JetBrains Mono',monospace; }
        .metric-card .metric-label { font-size:0.72rem; color:var(--text-muted); margin-top:0.3rem; text-transform:uppercase; letter-spacing:1px; }
        .page-header { background:linear-gradient(135deg,#073642,rgba(38,139,210,0.08)); border:1px solid var(--border); border-radius:14px; padding:1.5rem 1.8rem; margin-bottom:1.8rem; }
        .page-header h1 { background:var(--grad); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; font-size:2rem; font-weight:800; margin:0; }
        .page-header p { color:var(--text-muted); margin:0; font-size:0.9rem; }
        .stButton > button { background:var(--grad) !important; color:white !important; border:none !important; border-radius:8px !important; font-weight:600 !important; }
        section[data-testid="stSidebar"] { background:linear-gradient(180deg,#073642,#002B36); border-right:1px solid var(--border); }
    </style>
    """,
}


def apply_theme(theme_name: str = "Dark"):
    """Inject Google Fonts + CSS theme into the page."""
    _inject_fonts()
    css = THEMES.get(theme_name, THEMES["Dark"])
    st.markdown(css, unsafe_allow_html=True)


def get_theme():
    return st.session_state.get("theme", "Dark")


def require_auth():
    """Bypasses authentication as requested."""
    # Sync user settings from DB once per session
    if not st.session_state.get("_settings_loaded"):
        try:
            from database import get_db, User, UserSetting

            db = next(get_db(st.session_state.get("db_url")))
            username = st.session_state.get("username", "admin")
            if username:
                user = db.query(User).filter(User.username == username).first()
                if not user:
                    user = User(username=username, email=f"{username}@focusflow.app")
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                if not user.settings:
                    user.settings = UserSetting(user_id=user.id)
                    db.commit()

                settings_obj = user.settings
                if settings_obj and settings_obj.extra_config:
                    existing = st.session_state.get("settings_config", {})
                    st.session_state["settings_config"] = {**existing, **settings_obj.extra_config}

                st.session_state["troll_mode"] = bool(settings_obj.troll_mode) if settings_obj else st.session_state.get("troll_mode", True)
                st.session_state["nudge_only"] = bool(settings_obj.nudge_only) if settings_obj else st.session_state.get("nudge_only", False)
                if settings_obj and settings_obj.theme:
                    st.session_state["theme"] = settings_obj.theme
                if settings_obj and settings_obj.nudge_sensitivity:
                    st.session_state["nudge_sensitivity"] = settings_obj.nudge_sensitivity
                if settings_obj:
                    st.session_state["notification_sound"] = settings_obj.notification_sound
                    st.session_state["webcam_source"] = settings_obj.webcam_source
                    st.session_state["export_preference"] = settings_obj.export_preference
                    st.session_state["bot_training_enabled"] = settings_obj.bot_training_enabled
            db.close()
            st.session_state["_settings_loaded"] = True
        except Exception:
            # Non-fatal: settings will fall back to defaults
            st.session_state["_settings_loaded"] = True


def get_current_user_id(db):
    """Get (or create) the User row for the logged-in username."""
    from database import User
    username = st.session_state.get("username", "admin")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username, email=f"{username}@focusflow.app")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user.id


def format_duration(seconds):
    """Convert seconds → human-readable string e.g. '12m 5s'."""
    if not seconds or seconds < 0:
        return "0s"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def render_metric_card(label: str, value: str, icon: str = "📊", tooltip: str = ""):
    """Render a styled metric card."""
    title = f'title="{tooltip}"' if tooltip else ""
    st.markdown(f"""
    <div class="metric-card" {title}>
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = ""):
    """Render a styled page header banner."""
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f"""
    <div class="page-header">
        <h1>{title}</h1>
        {sub}
    </div>
    """, unsafe_allow_html=True)


def generate_fake_session_data(duration_minutes: int = 30):
    """Generate realistic demo engagement data."""
    sample_count = duration_minutes * 30

    timestamps, scores, ear_vals, gaze_vals = [], [], [], []
    yaw_vals, pitch_vals, distracted, spoof = [], [], [], []

    base = datetime.now() - timedelta(minutes=duration_minutes)
    score = 75.0
    trend = 0.0

    for i in range(sample_count):
        timestamps.append(base + timedelta(seconds=i * 2))
        dip = 0.0
        if random.random() < 0.07:
            dip = random.uniform(20, 45)
            trend = -2.0
        else:
            trend = min(trend + 0.5, 0.0)
        score = float(max(0, min(100, score + trend + random.uniform(-5, 5) - dip)))
        scores.append(round(score, 1))
        ear_vals.append(round(random.uniform(0.22, 0.38) if score > 40 else random.uniform(0.15, 0.25), 3))
        gaze_vals.append(round(max(0, min(1, score / 100 + random.uniform(-0.1, 0.1))), 2))
        yaw_vals.append(round(random.uniform(-10, 10) if score > 50 else random.uniform(-40, 40), 1))
        pitch_vals.append(round(random.uniform(-8, 8) if score > 50 else random.uniform(-25, 25), 1))
        distracted.append(score < 45)
        spoof.append(False)

    return {
        "timestamps": timestamps,
        "engagement_scores": scores,
        "ear_values": ear_vals,
        "gaze_scores": gaze_vals,
        "head_yaw": yaw_vals,
        "head_pitch": pitch_vals,
        "is_distracted": distracted,
        "is_spoof": spoof,
        "duration_minutes": duration_minutes,
        "avg_engagement": round(float(np.mean(scores)), 1),
        "peak_engagement": round(float(max(scores)), 1),
        "total_distractions": sum(distracted),
    }


def init_session_defaults():
    """Initialize all session state defaults. Modified to bypass auth."""
    defaults = {
        # Auth (Bypassed)
        "authentication_status": True,
        "name": "Administrator",
        "username": "admin",
        # Troll / UI
        "troll_caught": False,
        "troll_mode": True,
        "nudge_only": False,
        "theme": "Dark",
        "nudge_sensitivity": "Medium",
        # Session tracking
        "current_session_id": None,
        "session_start_ts": None,
        "live_stats": {
            "scores": [],
            "timestamps": [],
            "distractions": 0,
            "gaze_scores": [],
            "ear_values": [],
        },
        "last_troll_time": 0,
        "distraction_start_time": None,
        # Settings
        "notification_sound": True,
        "webcam_source": 0,
        "gemini_api_key": "",
        "bot_training_enabled": False,
        "export_preference": "Both",
        "db_url": None,
        "app_name": "Focus Flow",
        "language": "English",
        "focused_threshold": 70,
        "distracted_threshold": 40,
        # Spoof / mood
        "spoof_count": 0,
        "spoof_banner_dismissed": False,
        "spoof_banner_dismissed_at": 0,
        "mood_checked": False,
        "mood_score": None,
        "_settings_loaded": False,
        "last_log_ts": 0,
        # CV calibration data
        "user_calibration": None,
        "run_calibration": False,
        # Debug mode
        "debug_mode": False,
        # Nudge timer (fires at any score < 90%)
        "nudge_start_time": None,
    }
    # Consolidation for legacy pages
    if "settings_config" not in st.session_state:
        st.session_state["settings_config"] = {
            "app_name": defaults["app_name"],
            "focused_threshold": defaults["focused_threshold"],
            "distracted_threshold": defaults["distracted_threshold"],
            "gemini_api_key": defaults["gemini_api_key"],
            "language": defaults["language"],
            "theme": defaults["theme"],
            "auto_end_minutes": 10,
            "pomodoro_mode": False,
        }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def t(key):
    """Simple translation helper for legacy calls."""
    mapping = {
        "settings": "Settings",
        "about": "About",
        "dashboard": "Dashboard",
        "sessions": "Sessions",
        "analytics": "Analytics",
        "integrations": "Integrations",
        "coach": "AI Coach",
    }
    return mapping.get(key.lower(), key.capitalize())
