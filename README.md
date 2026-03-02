# 🧠 Focus Flow — Student Engagement Monitoring System

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/your-username/focus-flow/app.py)

An AI-powered study engagement monitoring system that uses your webcam to track focus, attention, and alertness during study sessions. Built with Streamlit, OpenCV, MediaPipe, and scikit-learn.

![Focus Flow Banner](https://img.shields.io/badge/Focus_Flow-v1.0.0-FF4B4B?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.42-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📹 **Live Webcam Analysis** | Real-time engagement tracking via MediaPipe face mesh |
| 👁️ **Eye Tracking (EAR)** | Drowsiness detection using Eye Aspect Ratio |
| 🖥️ **Head Pose Estimation** | Gaze direction via pitch/yaw/roll tracking |
| 🔍 **Iris Gaze Tracking** | Pupil position analysis for focus detection |
| 😮 **Expression Analysis** | Yawning and facial expression scoring |
| 🛡️ **Anti-Spoofing** | Detects static images/photos |
| 🤡 **Troll/Nudge System** | Fun animations when distracted (configurable!) |
| 🤖 **Gemini AI Coach** | AI-powered session reports and real-time suggestions |
| 📊 **Analytics Dashboard** | Per-session deep dive, comparisons, trends, heatmaps |
| 📄 **PDF & CSV Exports** | Professional session reports with embedded insights |
| 🧠 **ML Model Training** | Personalized engagement model (RandomForest, warm-start) |
| 🗄️ **Flexible Database** | SQLite (default) or PostgreSQL/Supabase |
| 🔌 **API Sidecar** | Optional FastAPI endpoints for webhooks and integrations |

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/focus-flow.git
cd focus-flow
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the App

```bash
streamlit run app.py
```

### 4. Login

Default credentials:
- **Username:** `student`
- **Password:** `student123`

---

## ☁️ Deploy to Streamlit Community Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **"New app"** → Select your repo → Set `app.py` as the main file
4. Add secrets in the Streamlit Cloud dashboard (optional):
   ```toml
   [secrets]
   GEMINI_API_KEY = "your-api-key"
   DATABASE_URL = "postgresql://..."
   ```
5. Deploy! 🎉

---

## 🐳 Docker Deployment

```bash
# Build and run
docker compose up --build

# Or just the app
docker build -t focus-flow .
docker run -p 8501:8501 focus-flow
```

---

## 🌐 Professional Hosting

### Railway
1. Connect your GitHub repo at [railway.app](https://railway.app)
2. Set environment variables: `DATABASE_URL`, `GEMINI_API_KEY`
3. Railway auto-detects the Dockerfile

### Render
1. Create a new **Web Service** at [render.com](https://render.com)
2. Connect your repo, set Docker environment
3. Add environment variables in the dashboard

### Heroku
```bash
heroku create focus-flow-app
heroku stack:set container
git push heroku main
heroku config:set DATABASE_URL=postgresql://...
```

---

## 📐 Engagement Score Formula

```
engagement_score = (
    0.35 × gaze_score +
    0.25 × head_pose_score +
    0.20 × ear_score +
    0.10 × presence_score +
    0.10 × expression_score
) × 100
```

---

## 🛠️ Tech Stack

- **Frontend/Framework:** Streamlit
- **Computer Vision:** OpenCV, MediaPipe
- **ML:** scikit-learn (RandomForestClassifier)
- **AI:** Google Gemini API
- **Database:** SQLite / PostgreSQL
- **Charts:** Plotly, Altair
- **Export:** FPDF2 (PDF), Pandas (CSV)
- **API:** FastAPI (optional sidecar)

---

## 📁 Project Structure

```
focus-flow/
├── app.py                    # Main entrypoint
├── database.py               # SQLAlchemy models & DB management
├── cv_engine.py              # Computer vision pipeline
├── ml_model.py               # ML engagement model
├── gemini_utils.py           # Gemini AI integration
├── exports.py                # PDF & CSV generation
├── utils.py                  # Shared utilities & themes
├── troll_system.py           # Troll/nudge engine
├── api_sidecar.py            # FastAPI endpoints (optional)
├── auth_config.yaml          # Authentication config
├── requirements.txt          # Python dependencies
├── packages.txt              # System packages (Streamlit Cloud)
├── Dockerfile                # Docker build
├── docker-compose.yml        # Docker Compose
├── .streamlit/
│   └── config.toml           # Streamlit configuration
├── ui_components/
│   └── troll_login.html      # Bouncing button animation
└── pages/
    ├── 0_Demo.py             # Demo (no login)
    ├── 1_Dashboard.py        # Live engagement dashboard
    ├── 3_Sessions.py         # Session management
    ├── 4_Analytics.py        # Analytics & trends
    ├── 5_Settings.py         # User settings
    ├── 6_About.py            # About page
    └── 7_Integrations.py     # Integration guides
```

---

## 📝 License

MIT License — Feel free to use, modify, and share.

---

## 👨‍💻 Author

Built with ❤️ by **SADA**

---

*Focus Flow v1.0.0*
