import streamlit as st # Comment

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from utils import (
    apply_theme, require_auth, render_page_header, 
    render_metric_card, get_current_user_id, t
)
from database import get_db, StudySession, EngagementLog

# ─── Auth Guard ─────────────────────────────────────────────────────────────
require_auth()

# ─── Page Setup ─────────────────────────────────────────────────────────────
app_name = st.session_state.get("settings_config", {}).get("app_name", "Focus Flow")
st.set_page_config(page_title=f"{app_name} - Analytics", page_icon="🧠", layout="wide")
apply_theme()

render_page_header(f"📊 {t('analytics')}", "Analyze your deep focus trends and patterns.")

# ─── Data Loading ────────────────────────────────────────────────────────────
db = next(get_db(st.session_state.get("db_url")))
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
    st.write("### 📈 Focus Summary")
    
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
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=40))
        st.plotly_chart(fig, use_container_width=True)

    # Mood & Focus Zone Distribution (Real Data)
    col_dist1, col_dist2 = st.columns(2)
    
    with col_dist1:
        st.write("### 🎭 Emotional Journey")
        mood_data = [s.mood_summary for s in completed if s.mood_summary]
        if mood_data:
            from collections import Counter
            m_counts = Counter(mood_data)
            m_df = pd.DataFrame([{'Mood': k, 'Sessions': v} for k, v in m_counts.items()])
            fig_m = px.pie(m_df, values='Sessions', names='Mood', hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_m.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300,
                               margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig_m, use_container_width=True)
        else:
            st.info("Record more sessions for mood analysis.")

    with col_dist2:
        st.write("### 🎯 Focus Zone Distribution")
        # Real-time distribution by querying all logs
        from sqlalchemy import text
        dist_sql = text("""
            SELECT 
              CASE 
                WHEN engagement_score >= 90 THEN 'Deep Focus'
                WHEN engagement_score >= 80 THEN 'Focused'
                WHEN engagement_score >= 36 THEN 'Neutral'
                ELSE 'Distracted'
              END as zone,
              COUNT(*) as count
            FROM engagement_logs
            JOIN sessions ON engagement_logs.session_id = sessions.id
            WHERE sessions.user_id = :u_id
            GROUP BY zone
        """)
        dist_res = db.execute(dist_sql, {"u_id": u_id}).fetchall()
        
        if dist_res:
            z_df = pd.DataFrame(dist_res, columns=['Zone', 'Count'])
            z_colors = {'Deep Focus': '#6C63FF', 'Focused': '#00D2FF', 'Neutral': '#FFD600', 'Distracted': '#FF4B4B'}
            fig_z = px.pie(z_df, values='Count', names='Zone', hole=0.4,
                          color='Zone', color_discrete_map=z_colors)
            fig_z.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300,
                               margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig_z, use_container_width=True)
        else:
            st.info("Complete a session to see focus distribution.")

    # Focus Forecast Card (Logic-driven)
    hour_scores = {}
    for s in completed:
        h = s.start_time.hour
        hour_scores.setdefault(h, []).append(s.avg_engagement)
    
    avg_hour = {h: np.mean(v) for h, v in hour_scores.items()}
    peak_h = max(avg_hour, key=avg_hour.get) if avg_hour else 0
    
    peak_mood = "Focused"
    if mood_data:
        from collections import Counter
        peak_mood = Counter(mood_data).most_common(1)[0][0]

    st.markdown(f"""
        <div class="glass-panel" style="border-left: 5px solid #FFD600; padding:1.2rem; margin-top:2rem;">
            <h3 style="margin:0 0 0.5rem 0;">🔮 Focus Forecast</h3>
            <p style="margin:0; opacity:0.9;">Based on your performance, your <b>Highest Quality Focus</b> usually happens at <b>{peak_h}:00</b>. 
            You tend to be <b>{peak_mood}</b> during your most productive hours. Plan your deep work accordingly!</p>
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
    st.write("### 📅 Weekly Focus Heatmap")
    
    # Calculate real daily averages
    days_map = {0:'Mon', 1:'Tue', 2:'Wed', 3:'Thu', 4:'Fri', 5:'Sat', 6:'Sun'}
    daily_stats = {d: [] for d in range(7)}
    for s in completed:
        daily_stats[s.start_time.weekday()].append(s.avg_engagement)
    
    heatmap_data = []
    for i in range(7):
        avg = np.mean(daily_stats[i]) if daily_stats[i] else 0
        heatmap_data.append({'Day': days_map[i], 'Avg Focus %': round(avg, 1)})
    
    h_df = pd.DataFrame(heatmap_data)
    
    fig_hm = px.bar(h_df, x='Day', y='Avg Focus %', color='Avg Focus %', 
                     color_continuous_scale='Viridis', labels={'Avg Focus %': 'Quality'})
    fig_hm.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,b=0,t=40),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_hm, use_container_width=True)
    
    # Attention Trends Logic
    if len(completed) >= 2:
        last_5 = completed[:5]
        prev_5 = completed[5:10]
        curr_avg = np.mean([s.avg_engagement for s in last_5])
        prev_avg = np.mean([s.avg_engagement for s in prev_5]) if prev_5 else curr_avg
        diff = curr_avg - prev_avg
        trend_text = f"increased by {abs(diff):.1f}%" if diff >= 0 else f"decreased by {abs(diff):.1f}%"
        
        st.markdown(f"""
            <div class="glass-panel" style="padding:1.2rem;">
                <h4 style="margin:0 0 0.5rem 0;">📈 Attention Trends</h4>
                <p style="margin:0; opacity:0.9;">Your average focus has <b>{trend_text}</b> compared to your previous sessions. 
                Keep hitting those targets! 🎯</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Complete more sessions to see long-term attention trends.")


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
