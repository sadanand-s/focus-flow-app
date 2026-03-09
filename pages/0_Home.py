"""
0_Home.py — Home page showing real session history from DB.
Shows actual engagement data from the user's past sessions.
If no sessions exist yet, provides a friendly first-run guide.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils import apply_theme, render_page_header, render_metric_card, get_current_user_id
from database import get_db, get_user_sessions, get_session_logs, StudySession

st.set_page_config(page_title="Home — Focus Flow", page_icon="🧠", layout="wide")
apply_theme(st.session_state.get("theme", "Dark"))

render_page_header("🏠 Home", "Your Focus Flow dashboard")

# ─── Load real sessions from DB ───────────────────────────────────────────────
db = next(get_db(st.session_state.get("db_url")))
try:
    user_id = get_current_user_id(db)
    all_sessions = get_user_sessions(db, user_id, status="completed")
    
    # ─── Lifetime Focus Stats (XP System) ──────────────────────────
    # Focus XP = Sum of (xp_earned) OR Fallback to (Duration * Engagement)
    total_xp = sum((s.xp_earned or (s.duration_seconds or 0) * (s.avg_engagement or 0) / 100) for s in all_sessions)
    
    # Define Ranks
    ranks = [
        (0, "Apprentice 🧑‍🎓", "#9E9E9E"),
        (1000, "Focused Scholar 📚", "#00D2FF"),
        (5000, "Attention Monk 🧘", "#6C63FF"),
        (15000, "Zen Master 🏮", "#FFD700"),
        (50000, "Focus Legend 🐉", "#FF5252")
    ]
    
    current_rank = ranks[0]
    next_rank = ranks[1]
    for i, r in enumerate(ranks):
        if total_xp >= r[0]:
            current_rank = r
            next_rank = ranks[i+1] if i+1 < len(ranks) else None
except Exception as e:
    all_sessions = []
    total_xp = 0
    current_rank = (0, "Apprentice 🧑‍🎓", "#9E9E9E")
    next_rank = None

# ─── No sessions yet: First-run guide ────────────────────────────────────────
if not all_sessions:
    st.markdown("""
    <div style="
        text-align:center; padding: 3rem 2rem;
        background: linear-gradient(135deg, rgba(108,99,255,0.08), rgba(0,210,255,0.04));
        border: 1px solid rgba(108,99,255,0.2); border-radius: 20px; margin-bottom: 2rem;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🧠</div>
        <h2 style="background: linear-gradient(135deg, #6C63FF, #00D2FF);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-size: 2rem; margin: 0 0 0.5rem 0;">Welcome to Focus Flow!</h2>
        <p style="color: #9E9E9E; font-size: 1.05rem; margin: 0 0 2rem 0;">
            You haven't completed any study sessions yet.<br>
            Head to the Dashboard, start a session, and come back here to see your real analytics!
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature highlight cards
    col1, col2, col3, col4 = st.columns(4)
    features = [
        ("📹", "Live Webcam", "Real-time engagement tracking via your camera"),
        ("🧠", "AI Scoring", "EAR, gaze, head pose all computed every frame"),
        ("🤡", "Troll Nudges", "Snarky popups when your attention drops"),
        ("📊", "Analytics", "Full session history and engagement trends"),
    ]
    for col, (icon, title, desc) in zip([col1, col2, col3, col4], features):
        with col:
            st.markdown(f"""
            <div style="background: rgba(108,99,255,0.08); border: 1px solid rgba(108,99,255,0.15);
                border-radius: 14px; padding: 1.25rem; text-align: center; height: 140px;
                display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 2rem; margin-bottom: 0.4rem;">{icon}</div>
                <div style="color: #E0E0E0; font-weight: 700; font-size: 0.95rem;">{title}</div>
                <div style="color: #9E9E9E; font-size: 0.78rem; margin-top: 0.3rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_start, _ = st.columns([1, 2])
    with col_start:
        if st.button("📹 Go to Dashboard & Start a Session", type="primary", use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")

    st.divider()
    db.close()
    st.stop()

# ─── Zen Level Progress Bar ──────────────────────────────────────────────────
if all_sessions:
    xp_limit = next_rank[0] if next_rank else current_rank[0]
    progress = min(1.0, total_xp / xp_limit) if xp_limit > 0 else 1.0
    
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); 
        border-radius:15px; padding:1.2rem; margin-bottom:2rem; display:flex; align-items:center; gap:20px;">
        <div style="font-size:3rem; min-width:80px; text-align:center;">{current_rank[1].split(' ')[1]}</div>
        <div style="flex-grow:1;">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px; align-items:flex-end;">
                <div>
                    <span style="color:#9E9E9E; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">Current Rank</span><br>
                    <b style="color:{current_rank[2]}; font-size:1.4rem;">{current_rank[1].split(' ')[0]}</b>
                </div>
                <div style="text-align:right;">
                    <span style="color:#9E9E9E; font-size:0.8rem;">{int(total_xp)} / {int(xp_limit)} XP</span>
                </div>
            </div>
            <div style="height:10px; background:rgba(255,255,255,0.05); border-radius:10px; overflow:hidden;">
                <div style="height:100%; width:{progress*100}%; background:linear-gradient(90deg, {current_rank[2]}, #FFF); 
                    box-shadow: 0 0 15px {current_rank[2]}44; border-radius:10px;"></div>
            </div>
            {f'<div style="font-size:0.75rem; color:#9E9E9E; margin-top:6px;">Target: Next level at {int(xp_limit)} XP</div>' if next_rank else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── Sessions exist — show real stats ─────────────────────────────────────────

# Pick session to view — default to latest
session_names = [f"#{s.id} — {s.name} ({s.tag})" for s in all_sessions]
selected_label = st.selectbox("📂 Select a session to view", session_names, index=0)
selected_idx   = session_names.index(selected_label)
selected       = all_sessions[selected_idx]

# ── Metric Cards ──────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
dur_s = selected.duration_seconds or 0
dur_str = f"{dur_s // 60}m {dur_s % 60}s" if dur_s >= 60 else f"{dur_s}s"

with col1:
    render_metric_card("Duration", dur_str, "⏱️")
with col2:
    render_metric_card("Avg Engagement", f"{selected.avg_engagement or 0:.1f}%", "📊")
with col3:
    render_metric_card("Peak Focus", f"{selected.peak_engagement or 0:.1f}%", "🎯")
with col4:
    render_metric_card("Distractions", str(selected.total_distractions or 0), "⚡")

st.markdown("<br>", unsafe_allow_html=True)

# ── Load engagement logs for selected session ──────────────────────────────────
logs = get_session_logs(db, selected.id)

if not logs:
    st.info("No engagement log data for this session yet. Logs are saved every 2 seconds during an active session.")
    db.close()
    st.stop()

# Build dataframe from logs
import pandas as pd
log_df = pd.DataFrame([{
    "Time":       log.timestamp,
    "Engagement": log.engagement_score or 0.0,
    "EAR":        log.ear_value or 0.0,
    "Gaze":       log.gaze_score or 0.0,
    "Head Yaw":   log.head_yaw or 0.0,
    "Head Pitch": log.head_pitch or 0.0,
    "Distracted": bool(log.is_distracted),
} for log in logs])

log_df["Time"] = pd.to_datetime(log_df["Time"])

# ── Charts ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 Engagement Timeline", "👁️ EAR / Drowsiness", "🎯 Gaze & Posture"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=log_df["Time"], y=log_df["Engagement"],
        mode="lines", name="Engagement",
        line=dict(color="#6C63FF", width=2),
        fill="tozeroy", fillcolor="rgba(108,99,255,0.08)",
    ))

    dist_df = log_df[log_df["Distracted"]]
    if not dist_df.empty:
        fig.add_trace(go.Scatter(
            x=dist_df["Time"], y=dist_df["Engagement"],
            mode="markers", name="Distraction",
            marker=dict(color="#FFB020", size=8, symbol="x"),
        ))

    fig.add_hline(y=80, line_dash="dot", line_color="#00E676", annotation_text="Focused (80%)")
    fig.add_hline(y=40, line_dash="dot", line_color="#FF5252", annotation_text="Distracted (40%)")
    fig.update_layout(
        title=f"Session #{selected.id} — {selected.name}",
        xaxis_title="Time", yaxis_title="Engagement %",
        yaxis=dict(range=[0, 105]),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,29,39,0.5)",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=log_df["Time"], y=log_df["EAR"],
        mode="lines", name="Eye Aspect Ratio",
        line=dict(color="#4BAFFF", width=2),
    ))
    fig2.add_hline(y=0.28, line_dash="dot",  line_color="#00E676",  annotation_text="Alert (0.28)")
    fig2.add_hline(y=0.22, line_dash="dash", line_color="#FFD600",  annotation_text="Drowsy (0.22)")
    fig2.add_hline(y=0.18, line_dash="dash", line_color="#FF5252",  annotation_text="Eyes Closed (0.18)")
    fig2.update_layout(
        title="Eye Aspect Ratio — Drowsiness Tracking",
        xaxis_title="Time", yaxis_title="EAR",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,29,39,0.5)",
        height=400,
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    col_a, col_b = st.columns(2)
    with col_a:
        fig3 = px.line(log_df, x="Time", y="Gaze", title="Gaze Score")
        fig3.update_layout(template="plotly_dark", height=350,
                           paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(26,29,39,0.5)")
        st.plotly_chart(fig3, use_container_width=True)
    with col_b:
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=log_df["Time"], y=log_df["Head Yaw"],
                                   mode="lines", name="Yaw", line=dict(color="#FFB020")))
        fig4.add_trace(go.Scatter(x=log_df["Time"], y=log_df["Head Pitch"],
                                   mode="lines", name="Pitch", line=dict(color="#00D26A")))
        fig4.add_hline(y=30,  line_dash="dot", line_color="red", annotation_text="Distraction Threshold")
        fig4.add_hline(y=-20, line_dash="dot", line_color="red")
        fig4.update_layout(title="Head Pose Angles", template="plotly_dark", height=350,
                           paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(26,29,39,0.5)")
        st.plotly_chart(fig4, use_container_width=True)

# ── Focus Distribution Pie ─────────────────────────────────────────────────────
st.subheader("📊 Focus Distribution")
focused_count    = int((~log_df["Distracted"]).sum())
distracted_count = int(log_df["Distracted"].sum())
pie_df = pd.DataFrame({"State": ["Focused", "Distracted"], "Count": [focused_count, distracted_count]})
fig5 = px.pie(pie_df, values="Count", names="State",
              color_discrete_sequence=["#00D26A", "#FF4B4B"], hole=0.4)
fig5.update_layout(template="plotly_dark", height=350, paper_bgcolor="rgba(0,0,0,0)")

col_pie, col_cta = st.columns([1, 1])
with col_pie:
    st.plotly_chart(fig5, use_container_width=True)
with col_cta:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    ### 📈 Session Summary
    **{selected.name}** · Tag: `{selected.tag}`
    
    - 🕐 Duration: **{dur_str}**
    - 📊 Average Engagement: **{selected.avg_engagement or 0:.1f}%**
    - 🏆 Peak Engagement: **{selected.peak_engagement or 0:.1f}%**
    - ⚡ Distractions: **{selected.total_distractions or 0}**
    - 🔢 Log entries: **{len(logs)}**
    """)
    if st.button("📹 Start New Session", type="primary", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")

# ─── All sessions summary at bottom ───────────────────────────────────────────
st.divider()
st.subheader(f"📋 All Sessions ({len(all_sessions)} total)")
summary_rows = []
for s in all_sessions:
    ds = s.duration_seconds or 0
    summary_rows.append({
        "ID":          f"#{s.id}",
        "Name":        s.name,
        "Tag":         s.tag,
        "Duration":    f"{ds // 60}m {ds % 60}s",
        "Avg Score":   f"{s.avg_engagement or 0:.1f}%",
        "Peak Score":  f"{s.peak_engagement or 0:.1f}%",
        "Distractions": s.total_distractions or 0,
    })
st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

db.close()
