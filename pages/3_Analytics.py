"""
4_Analytics.py — Deep analytics: session deep dive, comparison, trends, EAR tracking.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from utils import apply_theme, require_auth, render_page_header, get_current_user_id
from database import get_db, StudySession, EngagementLog, get_user_sessions, get_session_logs

st.set_page_config(page_title="Analytics — Focus Flow", page_icon="🧠", layout="wide")
apply_theme(st.session_state.get("theme", "Dark"))
require_auth()

render_page_header("📈 Analytics & Trends", "Deep dive into your study performance")

db = next(get_db())
user_id = get_current_user_id(db)
sessions = get_user_sessions(db, user_id)

if not sessions:
    st.info("📊 No session data available. Complete some study sessions to see analytics!")
    st.stop()

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_overview, tab_deepdive, tab_compare, tab_trends = st.tabs([
    "📊 Overview", "🔍 Deep Dive", "⚖️ Compare Sessions", "📈 Trends"
])

# ─── Overview Tab ─────────────────────────────────────────────────────────────
with tab_overview:
    st.subheader("Session Overview")

    # Build overview dataframe
    overview_data = []
    for s in sessions:
        overview_data.append({
            'Date': s.start_time,
            'Name': s.name,
            'Subject': s.tag,
            'Duration (min)': round((s.duration_seconds or 0) / 60, 1),
            'Avg Engagement': round(s.avg_engagement, 1),
            'Peak': round(s.peak_engagement, 1),
            'Distractions': s.total_distractions,
            'Status': s.status,
        })
    overview_df = pd.DataFrame(overview_data)

    # Engagement bar chart by session
    fig_bar = px.bar(
        overview_df, x='Date', y='Avg Engagement',
        color='Subject', hover_data=['Name', 'Duration (min)', 'Distractions'],
        title="Average Engagement Per Session",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_bar.add_hline(y=60, line_dash="dot", line_color="#00D26A",
                      annotation_text="Focus Goal (60%)")
    fig_bar.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    completed = [s for s in sessions if s.status == "completed"]
    with col1:
        st.metric("Total Sessions", len(sessions))
    with col2:
        total_mins = sum((s.duration_seconds or 0) for s in completed) / 60
        st.metric("Total Study Time", f"{total_mins:.0f} min")
    with col3:
        avg_all = np.mean([s.avg_engagement for s in completed]) if completed else 0
        st.metric("Overall Avg", f"{avg_all:.1f}%")
    with col4:
        total_dist = sum(s.total_distractions for s in completed)
        st.metric("Total Distractions", total_dist)

    # Data table
    st.dataframe(overview_df, use_container_width=True)

# ─── Deep Dive Tab ────────────────────────────────────────────────────────────
with tab_deepdive:
    st.subheader("Session Deep Dive")

    completed_sessions = [s for s in sessions if s.status == "completed"]
    if not completed_sessions:
        st.info("No completed sessions to analyze.")
    else:
        selected = st.selectbox(
            "Select a session:",
            completed_sessions,
            format_func=lambda s: f"{s.name} ({s.tag}) — {s.start_time.strftime('%Y-%m-%d %H:%M')}",
            key="deepdive_select",
        )

        if selected:
            logs = get_session_logs(db, selected.id)
            if not logs:
                st.info("No detailed logs for this session.")
            else:
                log_df = pd.DataFrame([{
                    'Time': l.timestamp,
                    'Engagement': l.engagement_score,
                    'EAR': l.ear_value,
                    'Gaze': l.gaze_score,
                    'Pitch': l.head_pitch,
                    'Yaw': l.head_yaw,
                    'Expression': l.expression_score,
                    'Distracted': l.is_distracted,
                    'Spoof': l.is_spoof,
                } for l in logs])

                # Engagement timeline with distraction markers
                fig_timeline = go.Figure()
                fig_timeline.add_trace(go.Scatter(
                    x=log_df['Time'], y=log_df['Engagement'],
                    mode='lines', name='Engagement',
                    line=dict(color='#FF4B4B', width=2),
                    fill='tozeroy', fillcolor='rgba(255,75,75,0.1)',
                ))
                dist_df = log_df[log_df['Distracted'] == True]
                if not dist_df.empty:
                    fig_timeline.add_trace(go.Scatter(
                        x=dist_df['Time'], y=dist_df['Engagement'],
                        mode='markers', name='Distraction',
                        marker=dict(color='#FFB020', size=7, symbol='x'),
                    ))
                fig_timeline.add_hline(y=60, line_dash="dot", line_color="#00D26A")
                fig_timeline.update_layout(title="Engagement Timeline",
                                           template="plotly_dark", height=350)
                st.plotly_chart(fig_timeline, use_container_width=True)

                # EAR + Gaze charts
                col_ear, col_gaze = st.columns(2)
                with col_ear:
                    fig_ear = go.Figure()
                    fig_ear.add_trace(go.Scatter(
                        x=log_df['Time'], y=log_df['EAR'],
                        mode='lines', name='EAR',
                        line=dict(color='#4BAFFF', width=2),
                    ))
                    fig_ear.add_hline(y=0.25, line_dash="dash", line_color="red",
                                      annotation_text="Drowsy Threshold")
                    fig_ear.update_layout(title="EAR (Drowsiness)",
                                          template="plotly_dark", height=300)
                    st.plotly_chart(fig_ear, use_container_width=True)

                with col_gaze:
                    fig_gaze = go.Figure()
                    fig_gaze.add_trace(go.Scatter(
                        x=log_df['Time'], y=log_df['Gaze'],
                        mode='lines', name='Gaze Score',
                        line=dict(color='#00D26A', width=2),
                    ))
                    fig_gaze.update_layout(title="Gaze Centrality",
                                           template="plotly_dark", height=300)
                    st.plotly_chart(fig_gaze, use_container_width=True)

                # Focus distribution
                col_pie, col_stats = st.columns(2)
                with col_pie:
                    focused = len(log_df[log_df['Distracted'] == False])
                    distracted = len(log_df[log_df['Distracted'] == True])
                    fig_pie = px.pie(
                        values=[focused, distracted],
                        names=['Focused', 'Distracted'],
                        color_discrete_sequence=['#00D26A', '#FF4B4B'],
                        hole=0.4, title="Focus Distribution",
                    )
                    fig_pie.update_layout(template="plotly_dark", height=300)
                    st.plotly_chart(fig_pie, use_container_width=True)

                with col_stats:
                    st.markdown("### 📊 Session Stats")
                    st.metric("Avg Engagement", f"{log_df['Engagement'].mean():.1f}%")
                    st.metric("Max Engagement", f"{log_df['Engagement'].max():.1f}%")
                    st.metric("Min Engagement", f"{log_df['Engagement'].min():.1f}%")
                    st.metric("Avg EAR", f"{log_df['EAR'].mean():.3f}")
                    focus_pct = (focused / max(1, focused + distracted)) * 100
                    st.metric("Focus %", f"{focus_pct:.1f}%")


# ─── Compare Tab ──────────────────────────────────────────────────────────────
with tab_compare:
    st.subheader("⚖️ Compare Two Sessions")

    completed_sessions = [s for s in sessions if s.status == "completed"]
    if len(completed_sessions) < 2:
        st.info("Need at least 2 completed sessions to compare.")
    else:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            s1 = st.selectbox("Session A:", completed_sessions,
                              format_func=lambda s: f"{s.name} ({s.start_time.strftime('%m/%d')})",
                              key="compare_s1")
        with col_s2:
            remaining = [s for s in completed_sessions if s.id != (s1.id if s1 else -1)]
            s2 = st.selectbox("Session B:", remaining,
                              format_func=lambda s: f"{s.name} ({s.start_time.strftime('%m/%d')})",
                              key="compare_s2")

        if s1 and s2:
            # Comparison table
            comp_data = {
                'Metric': ['Duration', 'Avg Engagement', 'Peak Engagement',
                           'Distractions', 'Subject'],
                f'{s1.name}': [
                    f"{(s1.duration_seconds or 0) / 60:.1f} min",
                    f"{s1.avg_engagement:.1f}%", f"{s1.peak_engagement:.1f}%",
                    str(s1.total_distractions), s1.tag,
                ],
                f'{s2.name}': [
                    f"{(s2.duration_seconds or 0) / 60:.1f} min",
                    f"{s2.avg_engagement:.1f}%", f"{s2.peak_engagement:.1f}%",
                    str(s2.total_distractions), s2.tag,
                ],
            }
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

            # Side-by-side charts
            logs1 = get_session_logs(db, s1.id)
            logs2 = get_session_logs(db, s2.id)

            col_c1, col_c2 = st.columns(2)
            for col, session_obj, session_logs in [(col_c1, s1, logs1), (col_c2, s2, logs2)]:
                with col:
                    if session_logs:
                        ldf = pd.DataFrame([{
                            'Time': l.timestamp, 'Engagement': l.engagement_score,
                        } for l in session_logs])
                        fig = px.line(ldf, x='Time', y='Engagement',
                                      title=f"{session_obj.name}")
                        fig.update_layout(template="plotly_dark", height=250,
                                          yaxis=dict(range=[0, 105]))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No detailed logs.")


# ─── Trends Tab ──────────────────────────────────────────────────────────────
with tab_trends:
    st.subheader("📈 Performance Trends")

    completed_sessions = [s for s in sessions if s.status == "completed" and s.start_time]
    if not completed_sessions:
        st.info("No completed sessions for trend analysis.")
    else:
        # Weekly engagement trend
        trend_df = pd.DataFrame([{
            'Date': s.start_time.date(),
            'Engagement': s.avg_engagement,
            'Subject': s.tag,
            'Duration': (s.duration_seconds or 0) / 60,
        } for s in completed_sessions])

        # Weekly aggregate
        trend_df['Week'] = pd.to_datetime(trend_df['Date']).dt.isocalendar().week
        weekly = trend_df.groupby('Week').agg({
            'Engagement': 'mean', 'Duration': 'sum'
        }).reset_index()

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=weekly['Week'], y=weekly['Engagement'],
            name='Avg Engagement', marker_color='#FF4B4B',
        ))
        fig_trend.add_trace(go.Scatter(
            x=weekly['Week'], y=weekly['Duration'],
            mode='lines+markers', name='Total Minutes',
            yaxis='y2', line=dict(color='#4BAFFF'),
        ))
        fig_trend.update_layout(
            title="Weekly Performance",
            yaxis=dict(title="Avg Engagement %", range=[0, 105]),
            yaxis2=dict(title="Study Minutes", overlaying='y', side='right'),
            template="plotly_dark", height=400,
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        # Subject breakdown
        if len(trend_df['Subject'].unique()) > 1:
            subj_avg = trend_df.groupby('Subject')['Engagement'].mean().reset_index()
            fig_subj = px.bar(subj_avg, x='Subject', y='Engagement',
                              title="Engagement by Subject",
                              color='Subject',
                              color_discrete_sequence=px.colors.qualitative.Set2)
            fig_subj.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig_subj, use_container_width=True)

        # Attention heatmap (time of day vs engagement)
        heatmap_data = []
        for s in completed_sessions:
            logs = get_session_logs(db, s.id)
            for l in logs:
                if l.timestamp:
                    heatmap_data.append({
                        'Hour': l.timestamp.hour,
                        'Day': l.timestamp.strftime('%A'),
                        'Engagement': l.engagement_score,
                    })

        if heatmap_data:
            hm_df = pd.DataFrame(heatmap_data)
            hm_pivot = hm_df.pivot_table(values='Engagement', index='Day', columns='Hour', aggfunc='mean')
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            hm_pivot = hm_pivot.reindex([d for d in day_order if d in hm_pivot.index])

            fig_hm = px.imshow(hm_pivot, aspect="auto",
                               title="Attention Heatmap (Day × Hour)",
                               color_continuous_scale="RdYlGn",
                               labels=dict(x="Hour of Day", y="Day", color="Engagement %"))
            fig_hm.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig_hm, use_container_width=True)
