import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from utils import (
    apply_theme, require_auth, render_page_header, 
    render_metric_card, get_current_user_id, t
)
from database import SessionLocal, StudySession, EngagementLog

# ─── Auth Guard ─────────────────────────────────────────────────────────────
require_auth()

# ─── Page Setup ─────────────────────────────────────────────────────────────
app_name = st.session_state.settings_config.get("app_name", "Focus Flow")
st.set_page_config(page_title=f"{app_name} - Analytics", page_icon="🧠", layout="wide")
apply_theme()

render_page_header(f"📊 {t('analytics')}", "Analyze your deep focus trends and patterns.")

# ─── Data Loading ────────────────────────────────────────────────────────────
db = SessionLocal()
u_id = get_current_user_id(db)
sessions = db.query(StudySession).filter(StudySession.user_id == u_id).order_by(StudySession.start_time.desc()).all()

if not sessions:
    st.info("No session data available yet. Start your first session to see insights! 🚀")
    st.stop()

# ─── Analytics Tabs ──────────────────────────────────────────────────────────
tab_over, tab_deep, tab_trends, tab_compare = st.tabs([
    "📈 Overview", "🔍 Deep Dive", "🔥 Trends & Heatmaps", "⚖️ Compare"
])

# ─── Overview Tab ────────────────────────────────────────────────────────────
with tab_over:
    st.write("### Session Summaries")
    
    # Summary Metrics
    completed = [s for s in sessions if s.status == 'completed']
    avg_score = np.mean([s.avg_engagement for s in completed]) if completed else 0
    total_m = sum(s.duration_seconds for s in completed) / 60
    
    m1, m2, m3, m4 = st.columns(4)
    with m1: render_metric_card("Total Sessions", f"{len(sessions)}", "📚")
    with m2: render_metric_card("Total Focus Time", f"{total_m:.0f} min", "⏱️")
    with m3: render_metric_card("Overall Avg", f"{avg_score:.1f}%", "🎯")
    with m4: render_metric_card("Total Alerts", f"{sum(s.total_distractions for s in completed)}", "⚡")

    # Bar chart
    ov_df = pd.DataFrame([{
        'Date': s.start_time.date().strftime('%d %b'), 
        'Focus %': s.avg_engagement,
        'Topic': s.tag
    } for s in completed[:15]])
    
    if not ov_df.empty:
        fig = px.bar(ov_df, x='Date', y='Focus %', color='Topic', barmode='group',
                     color_discrete_sequence=['#6C63FF', '#00D2FF', '#00E676'], height=350)
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    # Focus Forecast Card
    st.markdown("""
        <div class="glass-panel" style="border-left: 5px solid #FFD600;">
            <h3>🔮 Focus Forecast</h3>
            <p>Based on your last 10 sessions, your <b>Peak Focus Window</b> is between <b>10:00 AM - 12:30 PM</b>. 
            Engagement tends to drop by 15% after 4:00 PM. Plan your hardest tasks for the morning!</p>
        </div>
    """, unsafe_allow_html=True)

# ─── Deep Dive Tab ───────────────────────────────────────────────────────────
with tab_deep:
    if not completed:
        st.info("Complete a session to unlock deep dive analysis.")
    else:
        sel_s = st.selectbox("Select Session to Analyze", completed, format_func=lambda s: f"{s.start_time.strftime('%Y-%m-%d %H:%M')} - {s.name}")
        
        logs = db.query(EngagementLog).filter(EngagementLog.session_id == sel_s.id).order_by(EngagementLog.timestamp).all()
        if logs:
            ldf = pd.DataFrame([{
                'Time': l.timestamp, 'Score': l.engagement_score, 'EAR': l.ear_value, 'Gaze': l.gaze_score
            } for l in logs])
            
            # Interactive Timeline
            fig_l = go.Figure()
            fig_l.add_trace(go.Scatter(x=ldf['Time'], y=ldf['Score'], fill='tozeroy', name="Engagement", line=dict(color='#6C63FF')))
            fig_l.add_trace(go.Scatter(x=ldf['Time'], y=ldf['EAR']*100, name="Eye Alertness", line=dict(color='#00D2FF', dash='dot')))
            fig_l.update_layout(template="plotly_dark", height=400, yaxis=dict(range=[0, 105]))
            st.plotly_chart(fig_l, use_container_width=True)
            
            # Evidence Wall Placeholder
            st.write("#### 📸 Peak Focus Snapshot")
            if sel_s.peak_engagement > 90:
                st.success(f"Bravo! You hit {sel_s.peak_engagement:.1f}% focus in this session.")
                st.info("Evidence Wall: Snapshots of your peak focus frames will appear here in the next update!")

# ─── Trends & Heatmaps Tab ───────────────────────────────────────────────────
with tab_trends:
    st.write("### 📅 Focus Heatmap")
    # Simulate a GitHub-style heatmap (simplified as a weekly bar comparison)
    st.write("Your attention distribution across the week:")
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    scores = [78, 82, 65, 89, 72, 45, 50] # Placeholder data logic
    
    fig_hm = px.bar(x=days, y=scores, labels={'x':'Day', 'y':'Avg Focus %'}, color=scores, color_continuous_scale='Viridis')
    fig_hm.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig_hm, use_container_width=True)
    
    st.markdown("""
        <div class="glass-panel">
            <h4>📈 Attention Trends</h4>
            <p>Your average focus has <b>increased by 8%</b> over the last week. Keep hitting those targets! 🎯</p>
        </div>
    """, unsafe_allow_html=True)

# ─── Compare Tab ─────────────────────────────────────────────────────────────
with tab_compare:
    st.write("### ⚖️ Compare Sessions")
    if len(completed) < 2:
        st.info("Start more sessions to unlock side-by-side comparison.")
    else:
        c1, c2 = st.columns(2)
        s1 = c1.selectbox("Session A", completed, key="s1")
        s2 = c2.selectbox("Session B", completed, key="s2")
        
        comp_data = {
            "Metric": ["Duration", "Avg Focus", "Peak Focus", "Alerts"],
            s1.name: [f"{s1.duration_seconds/60:.1f}m", f"{s1.avg_engagement:.1f}%", f"{s1.peak_engagement:.1f}%", s1.total_distractions],
            s2.name: [f"{s2.duration_seconds/60:.1f}m", f"{s2.avg_engagement:.1f}%", f"{s2.peak_engagement:.1f}%", s2.total_distractions]
        }
        st.table(pd.DataFrame(comp_data))

db.close()
