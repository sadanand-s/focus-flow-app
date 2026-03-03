# 🧠 Focus Flow — AI Student Engagement System

![Focus Flow Banner](file:///C:/Users/SADA/.gemini/antigravity/brain/f2c3e77e-ff51-4f2e-8a9f-737833687ba4/focus_flow_banner_1772463390267.png)

[![Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://focus-flow.streamlit.app)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-34D058?style=flat-square&logo=python&logoColor=fff)
![Mediapipe](https://img.shields.io/badge/MediaPipe-Latest-007ACC?style=flat-square&logo=google&logoColor=fff)
![License](https://img.shields.io/badge/License-MIT-f39f37?style=flat-square)

---

### 🌟 Vision
**Focus Flow** is more than just a monitoring tool; it's a compassionate study partner. In a world of infinite distractions, we believe that the ability to concentrate is a superpower. Focus Flow uses cutting-edge computer vision and machine learning to help you reclaiming that power, one study session at a time.

Designed for students who demand the best, Focus Flow combines high-fidelity biometric tracking with a premium, glassmorphism-inspired UI and a snarky, personality-driven nudge system.

---

### ✨ Key Features

| 🚀 Power Features | 💎 Design & AI | 🔐 Privacy & Integration |
|:---:|:---:|:---:|
| **Live Biometric HUD**<br>Track Attention, EAR, & Posture. | **Premium Glassmorphism**<br>Vibrant dark mode aesthetics. | **Local-First Processing**<br>Biometrics stay on your machine. |
| **Iris Gaze Tracking**<br>Pinpoint accuracy on screen focus. | **AI Study Coach**<br>Gemini-powered personalized tips. | **Professional Exports**<br>Detailed PDF and CSV session reports. |
| **Smart Troll Nudges**<br>Fun popups when focus drifts. | **Confetti Easter Eggs**<br>Hidden rewards for interaction. | **Webhook Support**<br>Zapier/FastAPI integrations built-in. |
| **Anti-Spoofing**<br>Face variance & texture analysis. | **Multi-Language Engine**<br>English, Spanish, French, Hindi. | **Docker Ready**<br>Deploy globally with ease. |

---

### 🛠️ Developer Setup & Deployment

#### 1. Local Installation
```bash
# Clone the vision
git clone https://github.com/sadanand-s/focus-flow-app.git
cd focus-flow-app

# Create environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Run the Experience
```bash
streamlit run app.py
```

#### 3. Streamlit Cloud Hosting (GitHub)
Push this project to a GitHub repository. Streamlit Cloud will automatically detect `packages.txt` for OpenCV dependencies. Add your `GEMINI_API_KEY` in the **Advanced Settings > Secrets** tab of your Streamlit Dashboard.

---

### 📏 The Analytics Formula
Our **Unified Engagement Index (UEI)** combines five key metrics to derive your real-time focus percentage:
- **35%** Gaze Centrality
- **25%** Head Pose Stability
- **20%** Eye Aspect Ratio (EAR)
- **10%** Presence Score
- **10%** Micro-Expression Sampling

---

### 📂 Technical Stack
- **Frontend:** Streamlit 1.42.0 (Custom CSS / Glassmorphism)
- **Engine:** OpenCV Headerless, MediaPipe FaceMesh (468 pts)
- **ML:** Scikit-Learn RandomForest (Incremental Warm-start)
- **AI:** Google Gemini (Generative AI SDK)
- **Database:** SQLAlchemy / SQLite / Supabase

---

### 📂 Project Structure
- `app.py`: Main entry & Troll Login logic.
- `cv_engine.py`: Computer vision and pose estimation.
- `database.py`: Core DB schemas and persistence.
- `gemini_utils.py`: AI Coach and summary logic.
- `troll_system.py`: Chaos triggers for distractions.
- **Pages:**
  - `0_Demo.py`: No-login demo experience.
  - `1_Dashboard.py`: Live monitor & HUD.
  - `2_Sessions.py`: History & PDF export.
  - `3_Analytics.py`: Trends & Heatmaps.
  - `4_Settings.py`: Personalization & DB.
  - `5_About.py`: Vision & Science.
  - `6_Integrations.py`: Webhooks & OBS.
  - `7_AI_Coach.py`: Gemini-powered Chatbot.

---

### ❤️ Author & Inspiration
Created by **SADANAND** with the goal of helping students worldwide build the habit of deep focus. 

> "Efficiency is doing things right; effectiveness is doing the right things." — Peter Drucker. **Focus on what matters.**

---

*Focus Flow V2.1.0 — Empowering the next generation of thinkers.*
