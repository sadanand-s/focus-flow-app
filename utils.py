"""
utils.py — Shared utilities for the Student Engagement Monitoring System.
"""
import streamlit as st
import numpy as np
import random
from datetime import datetime, timedelta


# ─── Theme CSS ────────────────────────────────────────────────────────────────

THEMES = {
    "Dark": """
    <style>
        :root {
            --bg-primary: #0E1117;
            --bg-secondary: #1a1d26;
            --bg-card: #1e2130;
            --text-primary: #FAFAFA;
            --text-secondary: #B0B8C8;
            --accent: #FF4B4B;
            --accent-gradient: linear-gradient(135deg, #FF4B4B, #FF6B6B);
            --success: #00D26A;
            --warning: #FFB020;
            --border: #2D3348;
            --glass: rgba(30, 33, 48, 0.8);
        }
        .stApp { background-color: var(--bg-primary); }
        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 24px rgba(0,0,0,0.3);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 32px rgba(255,75,75,0.15);
        }
        .metric-card .metric-value {
            font-size: 2.2rem;
            font-weight: 800;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-card .metric-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .status-active {
            background: rgba(0,210,106,0.15);
            color: #00D26A;
            border: 1px solid rgba(0,210,106,0.3);
        }
        .status-completed {
            background: rgba(255,75,75,0.15);
            color: #FF4B4B;
            border: 1px solid rgba(255,75,75,0.3);
        }
        .page-header {
            background: linear-gradient(135deg, #1a1d26, #252838);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid var(--border);
        }
        .page-header h1 {
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
        }
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a1d26, #0E1117);
            border-right: 1px solid var(--border);
        }
        /* Input styling */
        .stTextInput > div > div > input,
        .stSelectbox > div > div {
            border-radius: 10px !important;
            border: 1px solid var(--border) !important;
        }
        /* Button styling */
        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(255,75,75,0.3);
        }
    </style>
    """,
    "Light": """
    <style>
        :root {
            --bg-primary: #FFFFFF;
            --bg-secondary: #F8F9FA;
            --bg-card: #FFFFFF;
            --text-primary: #1A1A2E;
            --text-secondary: #6C757D;
            --accent: #FF4B4B;
            --accent-gradient: linear-gradient(135deg, #FF4B4B, #FF6B6B);
            --success: #00C853;
            --warning: #FF9800;
            --border: #E0E0E0;
            --glass: rgba(255,255,255,0.9);
        }
        .stApp { background-color: var(--bg-primary); }
        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.12);
        }
        .metric-card .metric-value {
            font-size: 2.2rem;
            font-weight: 800;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-card .metric-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .status-active { background: rgba(0,200,83,0.12); color: #00C853; border: 1px solid rgba(0,200,83,0.3); }
        .status-completed { background: rgba(255,75,75,0.12); color: #FF4B4B; border: 1px solid rgba(255,75,75,0.3); }
        .page-header {
            background: linear-gradient(135deg, #F8F9FA, #E8EAF0);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid var(--border);
        }
        .page-header h1 {
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #F8F9FA, #FFFFFF);
            border-right: 1px solid var(--border);
        }
        .stButton > button { border-radius: 10px; font-weight: 600; }
    </style>
    """,
    "Solarized": """
    <style>
        :root {
            --bg-primary: #002B36;
            --bg-secondary: #073642;
            --bg-card: #073642;
            --text-primary: #FDF6E3;
            --text-secondary: #93A1A1;
            --accent: #B58900;
            --accent-gradient: linear-gradient(135deg, #B58900, #CB4B16);
            --success: #859900;
            --warning: #CB4B16;
            --border: #586E75;
            --glass: rgba(7,54,66,0.85);
        }
        .stApp { background-color: var(--bg-primary); }
        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 24px rgba(0,0,0,0.3);
            transition: transform 0.2s;
        }
        .metric-card:hover { transform: translateY(-4px); }
        .metric-card .metric-value {
            font-size: 2.2rem;
            font-weight: 800;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-card .metric-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .status-active { background: rgba(133,153,0,0.15); color: #859900; border: 1px solid rgba(133,153,0,0.3); }
        .status-completed { background: rgba(203,75,22,0.15); color: #CB4B16; border: 1px solid rgba(203,75,22,0.3); }
        .page-header {
            background: linear-gradient(135deg, #073642, #002B36);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid var(--border);
        }
        .page-header h1 {
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #073642, #002B36);
            border-right: 1px solid var(--border);
        }
        .stButton > button { border-radius: 10px; font-weight: 600; }
    </style>
    """,
}


def apply_theme(theme_name: str = "Dark"):
    """Inject CSS theme into the current Streamlit page."""
    css = THEMES.get(theme_name, THEMES["Dark"])
    st.markdown(css, unsafe_allow_html=True)


def get_theme():
    """Get current theme from session state."""
    return st.session_state.get("theme", "Dark")


def require_auth():
    """Check authentication and stop page if not authenticated."""
    if not st.session_state.get("authentication_status"):
        st.warning("🔒 Please login from the main page to access this feature.")
        st.stop()


def get_current_user_id(db):
    """Get or create User record from the auth username in session state."""
    from database import User
    username = st.session_state.get("username", "anonymous")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username, email=f"{username}@focusflow.app")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user.id


def format_duration(seconds):
    """Convert seconds to a human-readable duration string."""
    if seconds is None or seconds < 0:
        return "0s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def render_metric_card(label: str, value: str, icon: str = "📊"):
    """Render a styled metric card using custom HTML."""
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 1.5rem; margin-bottom: 0.3rem;">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = ""):
    """Render a styled page header."""
    sub_html = f'<p style="color: var(--text-secondary, #B0B8C8); margin-top: 0.5rem; font-size: 1rem;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="page-header">
        <h1>{title}</h1>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def generate_fake_session_data(duration_minutes: int = 30):
    """Generate realistic fake engagement data for the Demo page."""
    data_points = duration_minutes * 30  # ~30 fps equivalent, but we sample every 2s
    sample_count = duration_minutes * 30  # 30 samples per minute (every 2 seconds)

    timestamps = []
    engagement_scores = []
    ear_values = []
    gaze_scores = []
    head_yaw = []
    head_pitch = []
    is_distracted = []
    is_spoof = []

    base_time = datetime.now() - timedelta(minutes=duration_minutes)
    base_engagement = 75.0
    trend = 0.0

    for i in range(sample_count):
        t = base_time + timedelta(seconds=i * 2)
        timestamps.append(t)

        # Create realistic engagement patterns
        # Periodic dips (distraction events)
        dip = 0
        if random.random() < 0.08:  # 8% chance of distraction
            dip = random.uniform(20, 45)
            trend = -2.0
        elif random.random() < 0.03:  # 3% chance of major distraction
            dip = random.uniform(50, 70)
            trend = -5.0
        else:
            score = max(0.0, min(100.0, float(base_engagement + trend + random.uniform(-5, 5) - dip)))
        engagement_scores.append(round(score, 1))

        ear = round(float(random.uniform(0.22, 0.38) if score > 40 else random.uniform(0.15, 0.25)), 3)
        ear_values.append(ear)

        gaze = round(float(max(0.0, min(1.0, score / 100.0 + random.uniform(-0.1, 0.1)))), 2)
        gaze_scores.append(gaze)

        yaw = round(float(random.uniform(-10, 10) if score > 50 else random.uniform(-40, 40)), 1)
        head_yaw.append(yaw)
        pitch = round(float(random.uniform(-8, 8) if score > 50 else random.uniform(-25, 25)), 1)
        head_pitch.append(pitch)

        is_distracted.append(score < 45)
        is_spoof.append(False)

        base_engagement = score  # carry forward

    return {
        "timestamps": timestamps,
        "engagement_scores": engagement_scores,
        "ear_values": ear_values,
        "gaze_scores": gaze_scores,
        "head_yaw": head_yaw,
        "head_pitch": head_pitch,
        "is_distracted": is_distracted,
        "is_spoof": is_spoof,
        "duration_minutes": duration_minutes,
        "avg_engagement": round(float(np.mean(engagement_scores)), 1),
        "peak_engagement": round(float(max(engagement_scores)), 1),
        "total_distractions": sum(is_distracted),
    }


def init_session_defaults():
    """Initialize all session state defaults if not already set."""
    defaults = {
        "authentication_status": None,
        "name": None,
        "username": None,
        "troll_caught": False,
        "troll_mode": True,
        "nudge_only": False,
        "theme": "Dark",
        "nudge_sensitivity": "Medium",
        "notification_sound": True,
        "webcam_source": 0,
        "gemini_api_key": "",
        "bot_training_enabled": False,
        "export_preference": "Both",
        "current_session_id": None,
        "live_stats": {
            "scores": [],
            "timestamps": [],
            "distractions": 0,
            "gaze_scores": [],
            "ear_values": [],
        },
        "last_troll_time": 0,
        "distraction_start_time": None,
        "db_url": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
