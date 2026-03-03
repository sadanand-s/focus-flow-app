import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import SessionLocal, StudySession, User
from utils import apply_theme, require_auth, render_page_header, t, get_current_user_id
from gemini_utils import generate_coach_response
import io
import fpdf

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
db = SessionLocal()
u_id = get_current_user_id(db)
thirty_days_ago = datetime.now() - timedelta(days=30)
sessions = db.query(StudySession).filter(
    StudySession.user_id == u_id,
    StudySession.start_time >= thirty_days_ago,
    StudySession.status == 'completed'
).all()

# Create history summary
history_data = []
for s in sessions:
    history_data.append(f"Date: {s.start_time.date()}, Topic: {s.name}, Focus: {s.avg_engagement:.0f}%, Distractions: {s.total_distractions}")

history_summary = "\n".join(history_data[:10]) # Last 10 sessions for context
current_sess = "None"
if st.session_state.get('current_session_id'):
    current_sess = f"ID: {st.session_state['current_session_id']} active"

context = {
    "history_summary": history_summary,
    "current_session": current_sess,
    "thresholds": f"{st.session_state.get('settings_config', {}).get('focused_threshold', 70)}/{st.session_state.get('settings_config', {}).get('distracted_threshold', 40)}"
}

# ─── Sidebar: Progress Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.write("### 📈 Recent Progress")
    if sessions:
        avg_focus = sum(s.avg_engagement for s in sessions) / len(sessions)
        st.metric("30-Day Avg Focus", f"{avg_focus:.0f}%")
        
        # Simple mini bar chart of engagement
        progress_df = pd.DataFrame([s.avg_engagement for s in sessions], columns=["Focus %"])
        st.bar_chart(progress_df, height=150)
    else:
        st.info("No focus data for the last 30 days yet.")

    st.divider()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# ─── Suggested Questions ────────────────────────────────────────────────────
st.write("Suggested Topics:")
q_cols = st.columns(3)
suggestions = ["Analyze focus patterns", "Actionable focus tips", "Improve concentration"]
for i, sugg in enumerate(suggestions):
    if q_cols[i].button(sugg, use_container_width=True):
        st.session_state.user_query = sugg

# ─── Chat Interface ─────────────────────────────────────────────────────────
chat_container = st.container()

for msg in st.session_state.chat_history:
    with chat_container.chat_message("user" if msg["is_user"] else "assistant", avatar="🧑‍🎓" if msg["is_user"] else "🤖"):
        st.markdown(msg["text"])

user_input = st.chat_input("Ask about your focus patterns...")
if st.session_state.get("user_query"): # From suggestions
    user_input = st.session_state.user_query
    del st.session_state.user_query

if user_input:
    # Append user msg
    st.session_state.chat_history.append({"text": user_input, "is_user": True, "time": datetime.now()})
    with chat_container.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(user_input)
    
    # Generate bot msg
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
        pdf = fpdf.FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(40, 10, f"{app_name} AI Coach - Chat Report")
        pdf.ln(10)
        pdf.set_font("Arial", size=10)
        pdf.cell(40, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        pdf.ln(20)
        
        for msg in st.session_state.chat_history:
            role = "STUDENT" if msg["is_user"] else "COACH"
            pdf.set_font("Arial", 'B', 11)
            pdf.multi_cell(0, 10, f"{role}:")
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 10, msg["text"])
            pdf.ln(5)
            
        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 Download Report", pdf_bytes, "ai_coach_report.pdf", "application/pdf")

db.close()
