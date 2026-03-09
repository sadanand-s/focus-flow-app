import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_db, StudySession, get_training_dataset
from utils import apply_theme, require_auth, render_page_header, t, format_duration, render_metric_card, get_current_user_id
from exports import generate_pdf, generate_csv_from_db
from gemini_utils import generate_session_summary
from ml_model import EngagementModel

# ─── Auth Guard ─────────────────────────────────────────────────────────────
require_auth()

# ─── Page Setup ─────────────────────────────────────────────────────────────
app_name = st.session_state.get("settings_config", {}).get("app_name", "Focus Flow")
st.set_page_config(page_title=f"{app_name} - Sessions", page_icon="📚", layout="wide")
apply_theme()

render_page_header(f"📚 {t('sessions')}", "Review and manage your study history.")

# ─── Database Access ────────────────────────────────────────────────────────
db = next(get_db(st.session_state.get("db_url")))
u_id = get_current_user_id(db)
sessions = db.query(StudySession).filter(StudySession.user_id == u_id).order_by(StudySession.start_time.desc()).all()

if not sessions:
    st.info("No sessions recorded yet. Start one on the Dashboard! 🚀")
    st.stop()


@st.cache_resource
def _get_model():
    return EngagementModel()


labeled_completed = [s for s in sessions if s.status == "completed" and s.is_ground_truth]
train_col1, train_col2 = st.columns([2, 1])
with train_col1:
    st.info(
        f"Ground-truth sessions available for training: {len(labeled_completed)}. "
        "Label completed sessions, then train the model for better personalization."
    )
with train_col2:
    model = _get_model()
    if st.button("Train AI Model", use_container_width=True):
        features, labels = get_training_dataset(db, u_id)
        ok, acc = model.train(features, labels)
        if ok:
            st.success(f"Model trained successfully. Accuracy: {acc * 100:.1f}%")
        else:
            st.warning("Not enough balanced labeled data yet. Label more focused and distracted samples.")
    st.caption(f"Last accuracy: {model.get_accuracy() * 100:.1f}%")

# ─── Filter Bar ─────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    tag_filter = st.selectbox("🏷️ Filter by Subject", ["All"] + list(set(s.tag for s in sessions)))
with col_f2:
    status_filter = st.selectbox("📋 Status", ["All", "Active", "Completed"])
with col_f3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.write(f"Total: {len(sessions)} sessions")

# ─── Session List ──────────────────────────────────────────────────────────
st.divider()

for sess in sessions:
    # Apply Filters
    if tag_filter != "All" and sess.tag != tag_filter: continue
    if status_filter == "Active" and sess.status != "active": continue
    if status_filter == "Completed" and sess.status != "completed": continue
    
    # Determine Mood Icon
    mood_icons = {"Smiling": "😊", "Focused": "🎯", "Tired": "🥱", "Sleepy": "😴", "Yawning": "🥱", "Neutral": "😐"}
    mood_icon = mood_icons.get(sess.mood_summary, "📚")
    
    with st.expander(f"{mood_icon} {sess.start_time.strftime('%b %d, %H:%M')} — {sess.name} ({sess.tag})", expanded=(sess.status == 'active')):

        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            dur = format_duration(sess.duration_seconds) if sess.duration_seconds else "Active"
            render_metric_card("Duration", dur, "⏱️")
        with m2: render_metric_card("Avg Focus", f"{sess.avg_engagement:.1f}%", "🎯")
        with m3: render_metric_card("Peak Focus", f"{sess.peak_engagement:.1f}%", "⚡")
        with m4: render_metric_card("Alerts", f"{sess.total_distractions}", "⚡")
        
        # New Vision Metrics
        st.markdown(f"""
        <div style="display:flex; gap:10px; margin-top:5px;">
            <div style="background:rgba(255,255,255,0.05); border-radius:10px; padding:5px 12px; font-size:0.85rem; color:#9E9E9E;">
                🎭 Mood: <b style="color:#FFF;">{sess.mood_summary or 'Neutral'}</b>
            </div>
            <div style="background:rgba(255,215,0,0.1); border-radius:10px; padding:5px 12px; font-size:0.85rem; color:#FFD700;">
                🔥 XP Earned: <b style="color:#FFD700;">+{int(sess.xp_earned or 0)}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # AI Summary Section
        if sess.summary_text:
            st.markdown(f"""
                <div class="glass-panel" style="border-left: 4px solid #6C63FF; padding: 1.5rem;">
                    <h4>🤖 AI Summary</h4>
                    <p style="color:var(--text); opacity:0.9;">{sess.summary_text}</p>
                </div>
            """, unsafe_allow_html=True)
        
        # Ground Truth & Spoof Badges
        if sess.is_ground_truth or sess.spoof_detected:
            b1, b2 = st.columns(2)
            if sess.is_ground_truth: b1.success("🏷️ Labeled as Ground Truth")
            if sess.spoof_detected: b2.error("🚨 Anti-Spoofing Alert Detected")

        # Action Buttons
        st.divider()
        a1, a2, a3, a4 = st.columns(4)
        
        with a1:
            if st.button("📄 CSV Export", key=f"csv_{sess.id}", use_container_width=True):
                csv_data = generate_csv_from_db(db, sess.id)
                st.download_button("Download CSV", csv_data, f"session_{sess.id}.csv", "text/csv")
        
        with a2:
            if st.button("📑 PDF Report", key=f"pdf_{sess.id}", use_container_width=True):
                stats = {
                    'name': sess.name, 'tag': sess.tag, 'start_time': sess.start_time,
                    'duration_minutes': (sess.duration_seconds or 0)/60, 'avg_engagement': sess.avg_engagement,
                    'peak_engagement': sess.peak_engagement, 'total_distractions': sess.total_distractions,
                    'spoof_detected': sess.spoof_detected, 'focus_percentage': sess.avg_engagement
                }
                pdf_data = generate_pdf(stats, sess.summary_text or "No AI summary generated.")
                st.download_button("Download PDF", pdf_data, f"report_{sess.id}.pdf", "application/pdf")
        
        with a3:
            if not sess.summary_text and sess.status == 'completed':
                if st.button("🤖 AI Analysis", key=f"ai_{sess.id}", use_container_width=True):
                    with st.spinner("AI Analysis..."):
                        api_key = st.session_state.get("settings_config", {}).get("gemini_api_key", "")
                        summary = generate_session_summary(api_key, {
                            'name': sess.name, 'tag': sess.tag, 'duration': (sess.duration_seconds or 0)/60,
                            'avg_engagement': sess.avg_engagement, 'peak_engagement': sess.peak_engagement,
                            'distractions': sess.total_distractions, 'spoof_detected': sess.spoof_detected
                        })
                        sess.summary_text = summary
                        db.commit()
                        st.rerun()
        
        with a4:
            if not sess.is_ground_truth and sess.status == 'completed':
                if st.button("🏷️ Label Data", key=f"lab_{sess.id}", use_container_width=True):
                    sess.is_ground_truth = True
                    db.commit()
                    st.success("Data labeled for training! ✅")
                    st.rerun()

db.close()
