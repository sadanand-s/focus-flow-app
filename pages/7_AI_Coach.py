import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_db, StudySession, EngagementLog
from utils import apply_theme, require_auth, render_page_header, t, get_current_user_id
from gemini_utils import generate_coach_response
import io
from fpdf import FPDF
import plotly.express as px
import time

# ─── Auth Guard ─────────────────────────────────────────────────────────────
require_auth()

# ─── Page Setup ─────────────────────────────────────────────────────────────
app_name = st.session_state.get("settings_config", {}).get("app_name", "Focus Flow")
st.set_page_config(page_title=f"{app_name} - AI Progress Coach", page_icon="🤖", layout="wide")
apply_theme()

render_page_header(f"🤖 {t('coach')}", "Your personal AI study companion.")

# ─── Session State for Chat ──────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ─── Database & Context ──────────────────────────────────────────────────────
db = next(get_db(st.session_state.get("db_url")))
u_id = get_current_user_id(db)
thirty_days_ago = datetime.now() - timedelta(days=30)
sessions = db.query(StudySession).filter(
    StudySession.user_id == u_id,
    StudySession.start_time >= thirty_days_ago,
    StudySession.status == 'completed'
).order_by(StudySession.start_time.desc()).all()

# Create history summary
history_data = []
deep_history = []
for s in sessions:
    history_data.append(f"Date: {s.start_time.date()}, Topic: {s.name}, Focus: {s.avg_engagement:.0f}%, Distractions: {s.total_distractions}")
    
# Detailed analytics for top 3 recent sessions
for s in sessions[:3]:
    logs = db.query(EngagementLog).filter(EngagementLog.session_id == s.id).all()
    if logs:
        avg_ear = sum(l.ear_value for l in logs) / len(logs)
        avg_gaze = sum(l.gaze_score for l in logs) / len(logs)
        deep_history.append(f"Session {s.name}: Avg EAR {avg_ear:.2f}, Gaze {avg_gaze:.2f}")

history_summary = "\n".join(history_data[:10])
current_sess = f"ID: {st.session_state['current_session_id']} active" if st.session_state.get('current_session_id') else "None"

context = {
    "history_summary": history_summary,
    "deep_analytics": "\n".join(deep_history),
    "current_session": current_sess,
    "thresholds": f"{st.session_state.get('settings_config', {}).get('focused_threshold', 70)}/{st.session_state.get('settings_config', {}).get('distracted_threshold', 40)}"
}

# ─── Sidebar: Progress Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.write("### 📈 Recent Progress")
    if sessions:
        avg_focus = sum(s.avg_engagement for s in sessions) / len(sessions)
        st.metric("30-Day Avg Focus", f"{avg_focus:.0f}%")
        
        progress_df = pd.DataFrame([s.avg_engagement for s in reversed(sessions)], columns=["Focus %"])
        fig = px.line(progress_df, y="Focus %", height=200, markers=True)
        fig.update_layout(template="plotly_dark", margin=dict(l=0,r=0,t=0,b=0),
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No focus data for the last 30 days yet.")

    st.divider()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# ─── Suggested Questions ────────────────────────────────────────────────────
st.write("Suggested Topics:")
q_cols = st.columns(3)
suggestions = ["My focus patterns", " पोस्टरल थकान (Postural fatigue)?", "Improve concentration"]
for i, sugg in enumerate(suggestions):
    if q_cols[i].button(sugg, use_container_width=True):
        st.session_state.user_query = sugg

# ─── Chat Interface ─────────────────────────────────────────────────────────
chat_container = st.container()

for msg in st.session_state.chat_history:
    with chat_container.chat_message("user" if msg["is_user"] else "assistant", avatar="🧑‍🎓" if msg["is_user"] else "🤖"):
        st.markdown(msg["text"])

user_input = st.chat_input("Ask about your focus patterns...")
if st.session_state.get("user_query"):
    user_input = st.session_state.user_query
    del st.session_state.user_query

if user_input:
    st.session_state.chat_history.append({"text": user_input, "is_user": True, "time": datetime.now()})
    with chat_container.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(user_input)
    
    with chat_container.chat_message("assistant", avatar="🤖"):
        with st.spinner("AI Coach Thinking..."):
            api_key = st.session_state.get("settings_config", {}).get("gemini_api_key", "")
            response = generate_coach_response(api_key, user_input, st.session_state.chat_history, context)
            st.markdown(response)
            st.session_state.chat_history.append({"text": response, "is_user": False, "time": datetime.now()})

# ─── Export Chat ────────────────────────────────────────────────────────────
if st.session_state.chat_history:
    st.divider()
    if st.button("📄 Export Chat as PDF", use_container_width=True):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"{app_name} AI Coach - Chat Report", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(10)
        
        for msg in st.session_state.chat_history:
            role = "STUDENT" if msg["is_user"] else "COACH"
            pdf.set_font("Arial", 'B', 11)
            pdf.multi_cell(0, 10, f"{role}:")
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 8, msg.get("text", "").encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(5)
            
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Download Report", pdf_bytes, "ai_coach_report.pdf", "application/pdf")

db.close()
