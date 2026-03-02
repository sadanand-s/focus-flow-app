"""
3_Sessions.py — Session management: create, list, export, and label sessions.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from utils import apply_theme, require_auth, render_page_header, get_current_user_id, format_duration, render_metric_card
from database import get_db, StudySession, EngagementLog, get_user_sessions, get_session_logs
from exports import generate_csv_from_db, generate_pdf
from gemini_utils import generate_session_summary

st.set_page_config(page_title="Sessions — Focus Flow", page_icon="🧠", layout="wide")
apply_theme(st.session_state.get("theme", "Dark"))
require_auth()

render_page_header("📚 Study Sessions", "Manage, review, and export your study sessions")

db = next(get_db())
user_id = get_current_user_id(db)
sessions = get_user_sessions(db, user_id)

if not sessions:
    st.markdown("""
    <div style="text-align: center; padding: 3rem;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">📚</div>
        <h3 style="color: var(--text-secondary, #B0B8C8);">No sessions yet!</h3>
        <p style="color: var(--text-secondary, #888);">
            Go to the <b>Dashboard</b> to start your first study session.
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Filter controls
    col_filter1, col_filter2, col_filter3 = st.columns([1, 1, 1])
    with col_filter1:
        status_filter = st.selectbox("📋 Status", ["All", "Active", "Completed"])
    with col_filter2:
        tag_filter = st.selectbox("🏷️ Subject",
                                   ["All"] + list(set(s.tag for s in sessions if s.tag)))
    with col_filter3:
        sort_order = st.selectbox("📅 Sort", ["Newest First", "Oldest First"])

    # Apply filters
    filtered = sessions
    if status_filter != "All":
        filtered = [s for s in filtered if s.status == status_filter.lower()]
    if tag_filter != "All":
        filtered = [s for s in filtered if s.tag == tag_filter]
    if sort_order == "Oldest First":
        filtered = filtered[::-1]

    st.caption(f"Showing {len(filtered)} of {len(sessions)} sessions")
    st.divider()

    # Session cards
    for session in filtered:
        is_active = session.status == "active"
        status_class = "status-active" if is_active else "status-completed"
        status_text = "🟢 Active" if is_active else "✅ Completed"

        with st.expander(
            f"{'🟢' if is_active else '✅'} {session.name} — {session.tag} — "
            f"{session.start_time.strftime('%Y-%m-%d %H:%M') if session.start_time else 'N/A'}",
            expanded=False
        ):
            # Session info
            col_info1, col_info2, col_info3, col_info4 = st.columns(4)
            with col_info1:
                dur = format_duration(session.duration_seconds) if session.duration_seconds else "In progress"
                render_metric_card("Duration", dur, "⏱️")
            with col_info2:
                render_metric_card("Avg Engagement", f"{session.avg_engagement:.1f}%", "📊")
            with col_info3:
                render_metric_card("Peak Focus", f"{session.peak_engagement:.1f}%", "🎯")
            with col_info4:
                render_metric_card("Distractions", f"{session.total_distractions}", "⚡")

            st.markdown("<br>", unsafe_allow_html=True)

            # AI Summary
            if session.summary_text:
                with st.container():
                    st.markdown("**🤖 AI Summary:**")
                    st.info(session.summary_text)

            # Spoof warning
            if session.spoof_detected:
                st.warning("⚠️ Static image/photo was detected during this session.")

            # Ground truth label
            if session.is_ground_truth:
                st.success("🏷️ This session is labeled as **ground truth** for model training.")

            # Actions
            col_a1, col_a2, col_a3, col_a4 = st.columns(4)

            with col_a1:
                csv_data = generate_csv_from_db(db, session.id)
                st.download_button(
                    "📄 Download CSV",
                    data=csv_data,
                    file_name=f"session_{session.id}_{session.name}_export.csv",
                    mime="text/csv",
                    key=f"csv_{session.id}",
                    use_container_width=True,
                )

            with col_a2:
                session_data = {
                    'name': session.name,
                    'tag': session.tag,
                    'start_time': session.start_time,
                    'end_time': session.end_time,
                    'duration_minutes': (session.duration_seconds or 0) / 60,
                    'avg_engagement': session.avg_engagement,
                    'peak_engagement': session.peak_engagement,
                    'total_distractions': session.total_distractions,
                    'spoof_detected': session.spoof_detected,
                    'focus_percentage': max(0, 100 - (session.total_distractions / max(1, (session.duration_seconds or 1) / 2)) * 100),
                }
                pdf_data = generate_pdf(session_data, session.summary_text)
                st.download_button(
                    "📑 Download PDF",
                    data=pdf_data,
                    file_name=f"session_{session.id}_{session.name}_report.pdf",
                    mime="application/pdf",
                    key=f"pdf_{session.id}",
                    use_container_width=True,
                )

            with col_a3:
                if not session.summary_text:
                    if st.button("🤖 Generate AI Summary", key=f"ai_{session.id}",
                                 use_container_width=True):
                        api_key = st.session_state.get('gemini_api_key', '')
                        stats = {
                            'name': session.name,
                            'duration': (session.duration_seconds or 0) / 60,
                            'tag': session.tag,
                            'avg_engagement': session.avg_engagement,
                            'peak_engagement': session.peak_engagement,
                            'distractions': session.total_distractions,
                            'spoof_detected': session.spoof_detected,
                        }
                        summary = generate_session_summary(api_key, stats)
                        session.summary_text = summary
                        db.commit()
                        st.rerun()

            with col_a4:
                if not session.is_ground_truth and session.status == "completed":
                    if st.button("🏷️ Mark as Ground Truth", key=f"gt_{session.id}",
                                 use_container_width=True):
                        session.is_ground_truth = True
                        db.commit()
                        st.success("Marked as ground truth!")
                        st.rerun()
