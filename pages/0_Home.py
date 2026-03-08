"""
0_Home.py — Home page showing simulated engagement session (no login required).
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import apply_theme, generate_fake_session_data, render_page_header, render_metric_card

st.set_page_config(page_title="Home — Focus Flow", page_icon="🧠", layout="wide")
apply_theme(st.session_state.get("theme", "Dark"))

render_page_header("🏠 Home", "See how Focus Flow works")

# Generate fake data
if 'demo_data' not in st.session_state:
    st.session_state['demo_data'] = generate_fake_session_data(25)

data = st.session_state['demo_data']

# Metric cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_metric_card("Session Duration", f"{data['duration_minutes']}m", "⏱️")
with col2:
    render_metric_card("Avg Engagement", f"{data['avg_engagement']}%", "📊")
with col3:
    render_metric_card("Peak Focus", f"{data['peak_engagement']}%", "🎯")
with col4:
    render_metric_card("Distractions", f"{data['total_distractions']}", "⚡")

st.markdown("<br>", unsafe_allow_html=True)

# Engagement timeline
df = pd.DataFrame({
    'Time': data['timestamps'],
    'Engagement': data['engagement_scores'],
    'Distracted': data['is_distracted'],
})

tab1, tab2, tab3 = st.tabs(["📈 Engagement Timeline", "👁️ EAR / Drowsiness", "🎯 Gaze & Posture"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Time'], y=df['Engagement'],
        mode='lines', name='Engagement',
        line=dict(color='#FF4B4B', width=2),
        fill='tozeroy', fillcolor='rgba(255,75,75,0.1)',
    ))

    # Distraction markers
    dist_df = df[df['Distracted'] == True]
    if not dist_df.empty:
        fig.add_trace(go.Scatter(
            x=dist_df['Time'], y=dist_df['Engagement'],
            mode='markers', name='Distraction Event',
            marker=dict(color='#FFB020', size=8, symbol='x'),
        ))

    fig.add_hline(y=60, line_dash="dot", line_color="#00D26A",
                  annotation_text="Focus Threshold (60%)")
    fig.update_layout(
        title="Engagement Score Over Time",
        xaxis_title="Time", yaxis_title="Engagement %",
        yaxis=dict(range=[0, 105]),
        template="plotly_dark",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    ear_df = pd.DataFrame({
        'Time': data['timestamps'],
        'EAR': data['ear_values'],
    })
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=ear_df['Time'], y=ear_df['EAR'],
        mode='lines', name='Eye Aspect Ratio',
        line=dict(color='#4BAFFF', width=2),
    ))
    fig2.add_hline(y=0.25, line_dash="dash", line_color="#FF4B4B",
                   annotation_text="Drowsy Threshold (0.25)")
    fig2.update_layout(
        title="Eye Aspect Ratio (Drowsiness Tracking)",
        xaxis_title="Time", yaxis_title="EAR",
        template="plotly_dark", height=400,
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    pose_df = pd.DataFrame({
        'Time': data['timestamps'],
        'Gaze Score': data['gaze_scores'],
        'Head Yaw': data['head_yaw'],
        'Head Pitch': data['head_pitch'],
    })
    col_a, col_b = st.columns(2)
    with col_a:
        fig3 = px.line(pose_df, x='Time', y='Gaze Score',
                       title="Gaze Centrality Score")
        fig3.update_layout(template="plotly_dark", height=350)
        st.plotly_chart(fig3, use_container_width=True)
    with col_b:
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=pose_df['Time'], y=pose_df['Head Yaw'],
                                   mode='lines', name='Yaw', line=dict(color='#FFB020')))
        fig4.add_trace(go.Scatter(x=pose_df['Time'], y=pose_df['Head Pitch'],
                                   mode='lines', name='Pitch', line=dict(color='#00D26A')))
        fig4.add_hline(y=30, line_dash="dot", line_color="red", annotation_text="Distraction Threshold")
        fig4.add_hline(y=-30, line_dash="dot", line_color="red")
        fig4.update_layout(title="Head Pose Angles", template="plotly_dark", height=350)
        st.plotly_chart(fig4, use_container_width=True)

# Focus distribution
st.subheader("📊 Focus Distribution")
focused_time = sum(1 for d in data['is_distracted'] if not d)
distracted_time = sum(1 for d in data['is_distracted'] if d)
pie_df = pd.DataFrame({
    'State': ['Focused', 'Distracted'],
    'Count': [focused_time, distracted_time],
})
fig5 = px.pie(pie_df, values='Count', names='State',
              color_discrete_sequence=['#00D26A', '#FF4B4B'],
              hole=0.4)
fig5.update_layout(template="plotly_dark", height=350)
col_pie, col_cta = st.columns([1, 1])
with col_pie:
    st.plotly_chart(fig5, use_container_width=True)
with col_cta:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    ### 🚀 Start Tracking Live!

    Go to the **Live Dashboard** in the sidebar to start tracking your real study engagement with your webcam!

    The live version includes:
    - ✅ Real-time webcam analysis
    - ✅ AI-powered session reports
    - ✅ Personalized ML model training
    - ✅ Fun troll nudges when distracted
    - ✅ PDF & CSV exports
    """)

# Regenerate button
st.markdown("---")
if st.button("🔄 Regenerate Data"):
    st.session_state['demo_data'] = generate_fake_session_data(25)
    st.rerun()
