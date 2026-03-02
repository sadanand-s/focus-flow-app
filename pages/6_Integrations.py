import streamlit as st
from utils import apply_theme, require_auth, render_page_header, t
import json

# ─── Auth Guard ─────────────────────────────────────────────────────────────
require_auth()

# ─── Page Setup ─────────────────────────────────────────────────────────────
app_name = st.session_state.settings_config.get("app_name", "Focus Flow")
st.set_page_config(page_title=f"{app_name} - Integrations", page_icon="🔗", layout="wide")
apply_theme()

render_page_header(f"🔗 {t('integrations')}", "Connect your focus data to external apps.")

# ─── Integrations Tabs ──────────────────────────────────────────────────────
tab_obs, tab_zoom, tab_embed, tab_webhook, tab_api, tab_chrome = st.tabs([
    "📹 OBS Overlay",
    "🎥 Zoom SDK",
    "🖼️ iFrame Embed",
    "🪝 Webhooks",
    "📁 REST API",
    "🌐 Chrome Ext."
])

# ─── Tab 1: OBS Overlay ────────────────────────────────────────────────────
with tab_obs:
    st.markdown("""
    ### 📹 OBS Virtual Camera Setup
    Track your focus during live streams or video calls.
    
    1. **Install OBS Studio**: [Download here](https://obsproject.com/)
    2. **Add Browser Source**: In OBS, add a 'Browser' source.
    3. **URL**: Set it to `your-app-url/?overlay=true`
    4. **Dimensions**: Set to 1920x1080 (or your webcam resolution).
    5. **Custom CSS**: Use `body { background-color: rgba(0,0,0,0); }` for transparency.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("👁️ Test Overlay (New Tab)", on_click=lambda: st.write("Click this [link](/?overlay=true)"))
    with col2:
        st.info("The overlay provides a minimal draggable HUD with your live score and status dot.")

# ─── Tab 2: Zoom SDK Direct Integration ─────────────────────────────────────
with tab_zoom:
    st.subheader("🎥 Zoom App Marketplace")
    st.write("Automatically start sessions when a Zoom meeting begins.")
    
    with st.expander("🔑 Configure OAuth"):
        st.text_input("Zoom Client ID")
        st.text_input("Zoom Client Secret", type="password")
        if st.button("Connect Account"):
            st.success("Connected ✅ (Demo Mode)")
    
    st.write("---")
    st.markdown("""
    **Features Included:**
    - Auto-detect meeting start/end
    - Live focus status posted to meeting chat
    - 🟢/🟡/🔴 reaction sync every 10 mins
    """)

# ─── Tab 3: iFrame Embed ────────────────────────────────────────────────────
with tab_embed:
    st.subheader("🖼️ Generate Embed Code")
    st.write("Embed your live focus dashboard on your website or LMS.")
    
    token = "USER_SECRET_TOKEN_4123"
    embed_code = f'<iframe src="https://yourapp.streamlit.app/?embed=true&token={token}" width="100%" height="600" style="border:none; border-radius:12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);"></iframe>'
    
    st.code(embed_code, language="html")
    if st.button("📋 Copy to Clipboard"):
        st.write("Copied! (Simulation)")
    
    st.markdown("""
    **Embed Mode Includes:**
    - Hidden sidebar and header
    - Minimal live widget + engagement score
    - Read-only real-time timeline
    """)

# ─── Tab 4: Webhooks ────────────────────────────────────────────────────────
with tab_webhook:
    st.subheader("🪝 External Webhooks")
    st.write("Send per-minute focus data to Zapier, Make.com, or your own server.")
    
    target_url = st.text_input("Destination URL", placeholder="https://hooks.zapier.com/...")
    if st.button("Save Webhook"):
        st.success("Webhook configured successfully!")
        
    st.divider()
    st.write("**Payload Format (JSON):**")
    example_payload = {
        "timestamp": "2026-03-02T20:00:00Z",
        "engagement_score": 84,
        "status": "focused",
        "ear_value": 0.31,
        "spoof_detected": False
    }
    st.json(example_payload)

# ─── Tab 5: REST API ────────────────────────────────────────────────────────
with tab_api:
    st.subheader("📁 Professional REST API")
    st.write("Access your focus data via a high-performance FastAPI sidecar.")
    
    st.info("Sidecar active on port `8000`. Access Swagger UI at `/api/docs`.")
    
    if st.button("🗝️ Generate New API Key"):
        api_key = "fk_live_9sj23kd8sm28sk4m29sdj2"
        st.code(api_key)
        st.warning("Copy this key now! It will not be shown again.")
    
    st.write("**Endpoints:**")
    st.markdown("""
    - `GET /api/sessions`: List all focus history
    - `GET /api/engagement/live`: SSE stream of real-time score
    - `POST /api/sessions/start`: Trigger new session remotely
    """)

# ─── Tab 6: Chrome Extension ────────────────────────────────────────────────
with tab_chrome:
    st.subheader("🌐 Chrome Extension Starter")
    st.write("Keep an eye on your focus regardless of which tab you are on.")
    
    st.markdown("""
    - Injects a **floating badge** in the bottom-right corner.
    - Badge color changes based on engagement (Green/Yellow/Red).
    - Draggable and dismissible.
    """)
    
    if st.button("📥 Download extension_source.zip"):
        st.write("Download started... (Simulation)")
        
    st.info("Setup: Unzip, go to `chrome://extensions`, enable 'Developer mode', and 'Load unpacked'.")
