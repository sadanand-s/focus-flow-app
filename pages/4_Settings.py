import streamlit as st
import time
import os
import base64
from database import get_db, User, UserSetting, migrate_db
from utils import apply_theme, require_auth, render_page_header, t
import yaml

# ─── Auth Guard ─────────────────────────────────────────────────────────────
require_auth()

# ─── Page Setup ─────────────────────────────────────────────────────────────
app_name = st.session_state.get("settings_config", {}).get("app_name", "Focus Flow")
st.set_page_config(page_title=f"{app_name} - Settings", page_icon="⚙️", layout="wide")
apply_theme()

render_page_header(f"⚙️ {t('settings')}", "Personalize your focus environment.")

# ─── Load Settings from DB ──────────────────────────────────────────────────
db = next(get_db(st.session_state.get("db_url")))
username = st.session_state.get("username", "anonymous")
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

# Sync session state with DB if needed
if "settings_config" not in st.session_state:
    st.session_state.settings_config = settings_obj.extra_config or {}
elif settings_obj.extra_config:
    st.session_state.settings_config = {**st.session_state.settings_config, **settings_obj.extra_config}

# ─── Layout Tabs ────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎨 Identity & Layout", 
    "🕒 Session & Behavior", 
    "🔔 Alerts & Language",
    "🎧 Ambient",
    "🚀 Deployment & DB"
])

# ─── Tab 1: Identity & Layout ───────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🖼️ App Identity")
        new_app_name = st.text_input("Custom App Name", value=st.session_state.settings_config.get("app_name", "Focus Flow"))
        accent_color = st.color_picker("Global Accent Color", value=st.session_state.settings_config.get("accent_color", "#6C63FF"))
        
        avatar_file = st.file_uploader("Profile Avatar", type=['png', 'jpg', 'jpeg'])
        if avatar_file:
            bytes_data = avatar_file.getvalue()
            base64_avatar = base64.b64encode(bytes_data).decode()
            st.session_state.settings_config["avatar"] = f"data:image/png;base64,{base64_avatar}"
            st.success("Avatar uploaded!")

    with col2:
        st.subheader("📐 Dashboard Layout")
        st.write("Toggle widget visibility:")
        w_eng = st.toggle("Engagement Score Badge", value=st.session_state.settings_config.get("widgets", {}).get("engagement", True))
        w_ear = st.toggle("Eye Alertness Gauge", value=st.session_state.settings_config.get("widgets", {}).get("ear", True))
        w_pos = st.toggle("Posture/Yaw Score", value=st.session_state.settings_config.get("widgets", {}).get("posture", True))
        w_tim = st.toggle("Engagement Timeline", value=st.session_state.settings_config.get("widgets", {}).get("timeline", True))
        
        layout_mode = st.radio("Layout Density", ["Spacious", "Compact"], index=0 if st.session_state.settings_config.get("layout") == "Spacious" else 1)

# ─── Tab 2: Session & Behavior ──────────────────────────────────────────────
with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🎯 Engagement Thresholds")
        f_thresh = st.slider("Focused Threshold (%)", 50, 95, value=st.session_state.settings_config.get("focused_threshold", 70))
        d_thresh = st.slider("Distracted Threshold (%)", 10, 50, value=st.session_state.settings_config.get("distracted_threshold", 40))
        
        st.divider()
        st.subheader("⏳ Session Rules")
        auto_end = st.number_input("Auto-end session after N minutes of inactivity", 1, 60, value=st.session_state.settings_config.get("auto_end_minutes", 10))
        
    with col_b:
        st.subheader("🍅 Pomodoro Mode")
        pomo_on = st.toggle("Enable Pomodoro Intervals", value=st.session_state.settings_config.get("pomodoro_mode", False))
        if pomo_on:
            st.info("Sessions will auto-split into 25-min work / 5-min break blocks.")
        
        st.divider()
        st.subheader("🏷️ Custom Tags")
        st.write("Tag your sessions for better analytics (Coming soon)")

# ─── Tab 3: Alerts & Language ───────────────────────────────────────────────
with tab3:
    col_x, col_y = st.columns(2)
    with col_x:
        st.subheader("📢 Smart Nudges")
        st.session_state.troll_mode = st.toggle("Enable Troll/Nudge System", value=st.session_state.troll_mode)
        st.session_state.nudge_only = st.toggle("Nudge Only (Subtle toasts only)", value=st.session_state.nudge_only)
        
        n_delay = st.selectbox("Trigger delay (consecutive distraction)", [1, 2, 5], index=1)
        st.session_state.settings_config["n_delay"] = n_delay
        
        custom_msg = st.text_area("Custom Nudge Message", value=st.session_state.settings_config.get("custom_nudge_msg", "Stay focused! You got this."))

    with col_y:
        st.subheader("🌍 Localization")
        lang = st.selectbox("Preferred Language", ["English", "Spanish", "French", "Hindi"], index=["English", "Spanish", "French", "Hindi"].index(st.session_state.settings_config.get("language", "English")))

# ─── Tab 4: Ambient ────────────────────────────────────────────────────────
with tab4:
    st.subheader("🎶 Ambient Audio")
    st.write("Choose a background sound for your sessions.")
    ambient_opt = st.selectbox("Sound Type", ["None", "Lo-fi", "Rain", "White Noise", "Forest"], index=["None", "Lo-fi", "Rain", "White Noise", "Forest"].index(st.session_state.settings_config.get("ambient_sound", "None")))
    ambient_vol = st.slider("Volume", 0, 100, value=st.session_state.settings_config.get("ambient_volume", 50))
    
    st.info("Note: Ambient audio plays automatically during active sessions.")

# ─── Tab 5: Deployment & DB ───────────────────────────────────────────────
with tab5:
    st.subheader("🚀 Deployment Wizard")
    d_tab1, d_tab2, d_tab3 = st.tabs(["Streamlit Cloud", "Docker", "Database Migration"])
    
    with d_tab1:
        st.markdown("""
        ### Deploy to Streamlit Community Cloud (Free)
        1. Push this folder to a GitHub repository.
        2. Go to [share.streamlit.io](https://share.streamlit.io).
        3. Connect your repo and branch.
        4. Add your **Secrets** (Gemini API Key, etc.) in the Cloud dashboard.
        """)
        st.button("Open Streamlit Cloud")

    with d_tab2:
        st.markdown("### Self-host with Docker")
        st.code("""
docker-compose build
docker-compose up -d
        """, language="bash")
        st.write("Files generated: `Dockerfile`, `docker-compose.yml` are in your root folder.")

    with d_tab3:
        st.markdown("### Database Migration")
        new_db_url = st.text_input("New Database URL (PostgreSQL/Supabase/SQLite)", value="sqlite:///focus_flow.db")
        if st.button("Migrate & Connect"):
            with st.spinner("Testing connection..."):
                success, msg = migrate_db(new_db_url)
                if success:
                    st.success(msg)
                    st.session_state.db_url = new_db_url
                    os.environ["DATABASE_URL"] = new_db_url
                    st.session_state["_settings_loaded"] = False
                else:
                    st.error(msg)

# ─── Save All Actions ───────────────────────────────────────────────────────
st.divider()
if st.button("💾 Save All Personalized Settings", use_container_width=True):
    # Update session state config
    st.session_state.settings_config.update({
        "app_name": new_app_name,
        "accent_color": accent_color,
        "layout": layout_mode,
        "language": lang,
        "focused_threshold": f_thresh,
        "distracted_threshold": d_thresh,
        "auto_end_minutes": auto_end,
        "pomodoro_mode": pomo_on,
        "custom_nudge_msg": custom_msg,
        "ambient_sound": ambient_opt,
        "ambient_volume": ambient_vol,
        "widgets": {
            "engagement": w_eng,
            "ear": w_ear,
            "posture": w_pos,
            "timeline": w_tim
        }
    })
    
    # Save to DB
    settings_obj.extra_config = st.session_state.settings_config
    settings_obj.troll_mode = st.session_state.troll_mode
    settings_obj.nudge_only = st.session_state.nudge_only
    db.commit()
    st.session_state["_settings_loaded"] = True
    
    st.success("✅ Settings saved successfully! Rerunning app...")
    time.sleep(1)
    st.rerun()

db.close()
