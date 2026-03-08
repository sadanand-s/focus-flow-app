import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database import get_db, get_training_dataset, User, StudySession
from utils import apply_theme, require_auth, render_page_header, t, get_current_user_id
from ml_model import EngagementModel

# ─── Auth Guard ─────────────────────────────────────────────────────────────
require_auth()

# ─── Page Setup ─────────────────────────────────────────────────────────────
app_name = st.session_state.get("settings_config", {}).get("app_name", "Focus Flow")
st.set_page_config(page_title=f"{app_name} - AI Model Training", page_icon="🧠", layout="wide")
apply_theme()

render_page_header("🧠 AI Model Training Center", "Personalize your engagement detection for higher accuracy.")

# ─── Initialize Model ───────────────────────────────────────────────────────
@st.cache_resource
def get_model():
    return EngagementModel()

model = get_model()

# ─── Data Overview ──────────────────────────────────────────────────────────
db = next(get_db(st.session_state.get("db_url")))
u_id = get_current_user_id(db)

features, labels = get_training_dataset(db, u_id)
n_samples = len(features)
n_focused = sum(labels)
n_distracted = n_samples - n_focused

# ─── Layout: Stats Row ──────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Samples", n_samples)
with col2:
    st.metric("Focused Samples", n_focused, delta_color="normal")
with col3:
    st.metric("Distracted Samples", n_distracted, delta_color="inverse")
with col4:
    acc = model.get_accuracy()
    st.metric("Model Accuracy", f"{acc * 100:.1f}%")

st.divider()

# ─── Main content: Training Logic ───────────────────────────────────────────
col_info, col_action = st.columns([2, 1])

with col_info:
    st.subheader("📖 How Personalization Works")
    st.markdown("""
    The default engagement model uses a general heuristic and a pre-trained Random Forest. 
    To make it **yours**, you need to:
    1. **Mark Sessions**: Go to the **Sessions** page and click **Label Data** on sessions where your focus was accurately (or inaccurately) captured.
    2. **Diverse Data**: Try to label both highly focused sessions and sessions where you were legitimately distracted.
    3. **Retrain**: Click the button on the right to start the incremental training process.
    
    *Incremental training (Warm-start) allows the model to learn from new data without forgetting old patterns.*
    """)
    
    if n_samples < 10:
        st.warning("⚠️ **Low Data Warning**: You need at least 10 labeled samples for reliable training. Current: " + str(n_samples))
    elif n_focused == 0 or n_distracted == 0:
        st.warning("⚠️ **Imbalanced Data**: You need at least one sample of BOTH 'Focused' and 'Distracted' states.")

with col_action:
    st.subheader("⚡ Training Actions")
    
    can_train = n_samples >= 2 and n_focused > 0 and n_distracted > 0
    
    if st.button("🚀 Start Training Process", type="primary", use_container_width=True, disabled=not can_train):
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        status_placeholder.info("Fetching labeled data from database...")
        time.sleep(0.5)
        progress_bar.progress(30)
        
        status_placeholder.info("Preprocessing features and normalizing vectors...")
        time.sleep(0.5)
        progress_bar.progress(60)
        
        status_placeholder.info("Executing Incremental Random Forest training...")
        success, accuracy = model.train(features, labels)
        time.sleep(0.5)
        progress_bar.progress(100)
        
        if success:
            status_placeholder.success(f"✅ Training Complete! New Accuracy: {accuracy * 100:.1f}%")
            st.balloons()
            time.sleep(2)
            st.rerun()
        else:
            status_placeholder.error("❌ Training failed. Please check if you have enough diverse data.")

    if st.button("🗑️ Reset Model to Factory Defaults", use_container_width=True):
        if st.checkbox("I understand this will delete my personalized model weights."):
             if os.path.exists("engagement_model.pkl"):
                 os.remove("engagement_model.pkl")
             st.success("Model reset! Reloading...")
             time.sleep(1)
             st.rerun()

# ─── Training History Chart ─────────────────────────────────────────────────
st.divider()
st.subheader("📈 Accuracy History")

history = model.get_training_history()
if history:
    history_df = pd.DataFrame(history)
    history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
    
    fig = px.line(history_df, x='timestamp', y='accuracy', markers=True,
                  title="Model Accuracy Over Time",
                  labels={'accuracy': 'Accuracy', 'timestamp': 'Training Date'})
    
    fig.add_hline(y=0.7, line_dash="dot", line_color="orange", annotation_text="Target")
    fig.add_hline(y=0.9, line_dash="dot", line_color="green", annotation_text="Excellent")
    
    fig.update_layout(template="plotly_dark", 
                      paper_bgcolor='rgba(0,0,0,0)', 
                      plot_bgcolor='rgba(255,255,255,0.05)',
                      yaxis=dict(range=[0, 1.05]))
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No training history yet. Complete your first training session to see trends.")

# ─── Sample Data Preview ─────────────────────────────────────────────────────
with st.expander("🔍 Preview Labeled Data Samples"):
    if n_samples > 0:
        preview_df = pd.DataFrame(features, columns=["EAR", "Pitch", "Yaw", "Roll", "Gaze", "Expr"])
        preview_df['Label'] = ["Focused" if l == 1 else "Distracted" for l in labels]
        st.dataframe(preview_df.head(20), use_container_width=True)
    else:
        st.write("No labeled data found for preview.")

db.close()
