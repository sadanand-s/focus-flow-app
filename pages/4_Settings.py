"""
5_Settings.py — User settings: troll mode, theme, nudges, API keys, DB config, model training.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from datetime import datetime

from utils import apply_theme, require_auth, render_page_header
from database import get_db, get_engine, migrate_db, init_db, TrainingData, UserSetting
from ml_model import EngagementModel

st.set_page_config(page_title="Settings — Focus Flow", page_icon="🧠", layout="wide")
apply_theme(st.session_state.get("theme", "Dark"))
require_auth()

render_page_header("⚙️ Settings", "Customize your Focus Flow experience")

# ─── Troll & Nudge Settings ──────────────────────────────────────────────────
st.subheader("🤡 Troll & Nudge Mode")

col_t1, col_t2 = st.columns(2)
with col_t1:
    troll_mode = st.toggle("Enable Troll / Nudge Mode",
                            value=st.session_state.get('troll_mode', True),
                            help="When enabled, fun animations appear when you're distracted")
    st.session_state['troll_mode'] = troll_mode

with col_t2:
    if troll_mode:
        nudge_only = st.toggle("Nudge-Only Mode (no visual effects)",
                                value=st.session_state.get('nudge_only', False),
                                help="Show only toast notifications, no emoji storms or popups")
        st.session_state['nudge_only'] = nudge_only

if troll_mode:
    sensitivity = st.select_slider(
        "📢 Nudge Sensitivity",
        options=["Low", "Medium", "High"],
        value=st.session_state.get('nudge_sensitivity', 'Medium'),
        help="Low = trigger after 3min, Medium = 2min, High = 1min of distraction",
    )
    st.session_state['nudge_sensitivity'] = sensitivity

    notification_sound = st.toggle("🔊 Notification Sound",
                                    value=st.session_state.get('notification_sound', True))
    st.session_state['notification_sound'] = notification_sound

st.divider()

# ─── Appearance ──────────────────────────────────────────────────────────────
st.subheader("🎨 Appearance")

theme = st.selectbox(
    "Theme",
    ["Dark", "Light", "Solarized"],
    index=["Dark", "Light", "Solarized"].index(st.session_state.get('theme', 'Dark')),
)
if theme != st.session_state.get('theme'):
    st.session_state['theme'] = theme
    st.rerun()

st.divider()

# ─── Webcam ──────────────────────────────────────────────────────────────────
st.subheader("📹 Webcam")
webcam = st.number_input("Webcam Source Index", min_value=0, max_value=10,
                          value=st.session_state.get('webcam_source', 0),
                          help="0 = default camera, 1 = secondary camera, etc.")
st.session_state['webcam_source'] = webcam

st.divider()

# ─── Gemini API ──────────────────────────────────────────────────────────────
st.subheader("🤖 Gemini AI Integration")
st.caption("Your API key is stored in session only — never saved to the database.")

api_key = st.text_input(
    "Gemini API Key",
    value=st.session_state.get('gemini_api_key', ''),
    type="password",
    placeholder="Enter your Google Gemini API key...",
)
if st.button("💾 Save API Key"):
    st.session_state['gemini_api_key'] = api_key
    if api_key:
        st.success("✅ API key saved to session!")
    else:
        st.info("API key cleared. Template-based reports will be used.")

st.markdown("""
<details>
<summary>How to get a Gemini API key</summary>
<ol>
<li>Go to <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a></li>
<li>Click "Create API Key"</li>
<li>Copy the key and paste it above</li>
</ol>
</details>
""", unsafe_allow_html=True)

st.divider()

# ─── Bot Training ────────────────────────────────────────────────────────────
st.subheader("🧠 Real-Time Bot Training")

bot_training = st.toggle(
    "Enable Model Training",
    value=st.session_state.get('bot_training_enabled', False),
    help="Collect engagement data during sessions to train a personalized ML model",
)
st.session_state['bot_training_enabled'] = bot_training

if bot_training:
    st.info("📊 Training data will be collected during your sessions (with your consent).")

# Model status
try:
    model = EngagementModel()
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Model Status", "Trained ✅" if model.is_trained else "Not Trained ❌")
    with col_m2:
        st.metric("Last Trained", model.get_last_trained())
    with col_m3:
        st.metric("Last Accuracy", f"{model.get_accuracy() * 100:.1f}%" if model.is_trained else "N/A")

    # Training history chart
    history = model.get_training_history()
    if history:
        hist_df = pd.DataFrame(history)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(hist_df))), y=hist_df['accuracy'] * 100,
            mode='lines+markers', name='Accuracy',
            line=dict(color='#00D26A', width=2),
        ))
        fig.update_layout(
            title="Training Accuracy Over Time",
            yaxis=dict(title="Accuracy %", range=[0, 105]),
            xaxis=dict(title="Training Iteration"),
            template="plotly_dark", height=250,
        )
        st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"Could not load model info: {e}")

st.divider()

# ─── Export Preferences ──────────────────────────────────────────────────────
st.subheader("📄 Export Preferences")
export_pref = st.radio(
    "Default export format:",
    ["PDF", "CSV", "Both"],
    index=["PDF", "CSV", "Both"].index(st.session_state.get('export_preference', 'Both')),
    horizontal=True,
)
st.session_state['export_preference'] = export_pref

st.divider()

# ─── Database Configuration ──────────────────────────────────────────────────
st.subheader("🗄️ Database Configuration")

current_db = st.session_state.get('db_url', 'SQLite (Local)')
st.caption(f"Current: **{current_db if current_db else 'SQLite (Local, default)'}**")

with st.expander("🔗 Connect External Database (PostgreSQL / Supabase)"):
    db_url = st.text_input(
        "Connection String",
        placeholder="postgresql://user:password@host:5432/dbname",
        type="password",
    )
    if st.button("🔌 Connect & Migrate"):
        if db_url:
            with st.spinner("Connecting..."):
                success, msg = migrate_db(db_url)
                if success:
                    st.session_state['db_url'] = db_url
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")
        else:
            st.warning("Please enter a connection string.")

    if st.button("🔄 Reset to Local SQLite"):
        st.session_state['db_url'] = None
        st.success("Reset to local SQLite database.")

# Mini table viewer
with st.expander("📊 Database Table Viewer"):
    table_name = st.selectbox("Select Table",
                               ["users", "sessions", "engagement_logs", "settings", "training_data"])
    try:
        from sqlalchemy import text
        engine = get_engine(st.session_state.get('db_url'))
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 100"))
            rows = result.fetchall()
            cols = result.keys()
            if rows:
                st.dataframe(pd.DataFrame(rows, columns=cols), use_container_width=True)
            else:
                st.info("Table is empty.")
    except Exception as e:
        st.warning(f"Could not read table: {e}")

    # CSV import
    st.markdown("---")
    uploaded = st.file_uploader(f"📥 Import CSV into `{table_name}`", type="csv",
                                 key=f"upload_{table_name}")
    if uploaded:
        st.warning("⚠️ CSV import is available for advanced users. Ensure your CSV matches the table schema.")
        if st.button("Import", key=f"import_{table_name}"):
            st.info("CSV import functionality requires schema validation. Coming soon!")
