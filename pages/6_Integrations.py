"""
7_Integrations.py — Integration guides, iframe embed, OBS setup, webhooks, API keys.
"""
import streamlit as st
import uuid

from utils import apply_theme, require_auth, render_page_header

st.set_page_config(page_title="Integrations — Focus Flow", page_icon="🧠", layout="wide")
apply_theme(st.session_state.get("theme", "Dark"))
require_auth()

render_page_header("🔌 Integrations", "Connect Focus Flow with your workflow")

tab_embed, tab_obs, tab_extension, tab_webhook, tab_api = st.tabs([
    "🖼️ Iframe Embed", "📹 OBS Setup", "🧩 Browser Extension",
    "🔗 Webhooks", "🔑 API Keys"
])

# ─── Iframe Embed ─────────────────────────────────────────────────────────────
with tab_embed:
    st.subheader("🖼️ Embed Focus Flow in Your Website")
    st.markdown("Copy the iframe snippet below to embed Focus Flow in any webpage:")

    app_url = st.text_input("Your Focus Flow URL",
                             value="https://your-app.streamlit.app",
                             help="Replace with your actual deployed URL")

    embed_code = f"""<iframe
    src="{app_url}"
    width="100%"
    height="800"
    frameborder="0"
    allow="camera; microphone"
    style="border: 1px solid #2D3348; border-radius: 12px;"
></iframe>"""

    st.code(embed_code, language="html")
    st.button("📋 Copy to Clipboard", key="copy_iframe",
              help="Copy the embed code (use Ctrl+C on the code block)")

    st.info("""
    **Note:** For the webcam to work in an iframe, the parent page must:
    - Be served over HTTPS
    - Have the `allow="camera"` attribute on the iframe
    """)

# ─── OBS Virtual Camera ──────────────────────────────────────────────────────
with tab_obs:
    st.subheader("📹 OBS Virtual Camera Setup")
    st.markdown("""
    Use Focus Flow alongside Google Meet, Zoom, or Teams by routing your webcam
    through OBS Studio's virtual camera.
    """)

    st.markdown("""
    ### Setup Guide

    #### Step 1: Install OBS Studio
    Download from [obsproject.com](https://obsproject.com/) (free & open source).

    #### Step 2: Add Video Capture
    1. Open OBS Studio
    2. In **Sources**, click **+** → **Video Capture Device**
    3. Select your webcam
    4. Arrange the preview as desired

    #### Step 3: Start Virtual Camera
    1. Click **Start Virtual Camera** in OBS
    2. In Google Meet / Zoom / Teams, select **OBS Virtual Camera** as your camera

    #### Step 4: Use Focus Flow
    1. Open Focus Flow in your browser
    2. In Settings, set **Webcam Source** to your physical webcam index
    3. Start a session — Focus Flow will analyze your real camera feed
    4. Your meeting participants see the OBS virtual camera output

    ### Diagram
    ```
    Physical Webcam → Focus Flow (analysis)
                  ↘
                    OBS Studio → Virtual Camera → Google Meet / Zoom / Teams
    ```

    ### Pro Tips
    - Run Focus Flow on a secondary window/monitor
    - Use OBS scenes to switch between webcam views
    - Add overlays in OBS for a professional look
    """)

# ─── Browser Extension ───────────────────────────────────────────────────────
with tab_extension:
    st.subheader("🧩 Chrome Browser Extension (Coming Soon)")
    st.markdown("A Chrome extension that embeds Focus Flow engagement tracking directly in your browser.")

    st.markdown("### Manifest Template")
    manifest = """{
  "manifest_version": 3,
  "name": "Focus Flow - Engagement Tracker",
  "version": "1.0.0",
  "description": "Track your study engagement while browsing",
  "permissions": ["activeTab", "storage"],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "css": ["content.css"]
    }
  ],
  "background": {
    "service_worker": "background.js"
  }
}"""
    st.code(manifest, language="json")

    st.info("""
    **Status:** 🚧 The browser extension is a placeholder for future development.
    The manifest above provides the structure for a Chrome Extension that could:
    - Show engagement status in a popup
    - Inject a floating widget on study pages
    - Send engagement data to the Focus Flow API
    """)

# ─── Webhooks ─────────────────────────────────────────────────────────────────
with tab_webhook:
    st.subheader("🔗 Webhook Configuration")
    st.markdown("Set up webhooks to receive real-time engagement events as JSON POST requests.")

    # Generate webhook URL
    if 'webhook_id' not in st.session_state:
        st.session_state['webhook_id'] = str(uuid.uuid4())[:12]

    webhook_base = st.text_input("API Base URL", value="https://your-api.example.com",
                                  help="The base URL of your FastAPI sidecar or custom API")

    webhook_url = f"{webhook_base}/api/webhook/{st.session_state['webhook_id']}"
    st.code(webhook_url, language="text")

    if st.button("🔄 Regenerate Webhook ID"):
        st.session_state['webhook_id'] = str(uuid.uuid4())[:12]
        st.rerun()

    st.markdown("### Event Payload Format")
    payload_example = """{
  "event_type": "engagement_update",
  "timestamp": "2024-01-15T10:30:00Z",
  "session_id": 42,
  "user_id": 1,
  "data": {
    "engagement_score": 78.5,
    "is_distracted": false,
    "ear_value": 0.32,
    "gaze_score": 0.89,
    "head_pose": {"pitch": 5.2, "yaw": -3.1, "roll": 0.8}
  }
}"""
    st.code(payload_example, language="json")

    st.markdown("""
    ### Supported Events
    | Event Type | Description |
    |-----------|-------------|
    | `engagement_update` | Per-interval engagement metrics |
    | `session_start` | Session created |
    | `session_end` | Session completed |
    | `distraction_alert` | Extended distraction detected |
    | `spoof_detected` | Static image flagged |
    """)

# ─── API Keys ────────────────────────────────────────────────────────────────
with tab_api:
    st.subheader("🔑 API Key Management")
    st.markdown("Generate API keys for programmatic access to your Focus Flow data.")

    if 'api_keys' not in st.session_state:
        st.session_state['api_keys'] = []

    col_gen, col_list = st.columns([1, 2])

    with col_gen:
        key_name = st.text_input("Key Name", placeholder="my-integration")
        if st.button("🔑 Generate API Key", use_container_width=True):
            if key_name:
                new_key = f"ff_{uuid.uuid4().hex[:32]}"
                st.session_state['api_keys'].append({
                    'name': key_name,
                    'key': new_key,
                    'created': str(st.session_state.get('_now', 'now')),
                })
                st.success(f"✅ Key created!")
                st.code(new_key)
                st.warning("⚠️ Copy this key now — it won't be shown again in full.")
            else:
                st.warning("Please enter a key name.")

    with col_list:
        st.markdown("### Your API Keys")
        if st.session_state['api_keys']:
            for i, key_info in enumerate(st.session_state['api_keys']):
                masked = key_info['key'][:6] + "..." + key_info['key'][-4:]
                st.markdown(f"**{key_info['name']}**: `{masked}`")
                if st.button(f"🗑️ Revoke", key=f"revoke_{i}"):
                    st.session_state['api_keys'].pop(i)
                    st.rerun()
        else:
            st.info("No API keys generated yet.")

    st.markdown("""
    ### API Usage
    Include the API key in the `Authorization` header:
    ```bash
    curl -H "Authorization: Bearer ff_your_api_key_here" \\
         https://your-api.example.com/api/sessions
    ```
    """)
