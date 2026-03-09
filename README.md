# 🧠 Focus Flow — Student Engagement Monitor

Focus Flow is a personal study assistant that uses computer vision to track your engagement and help you stay focused during study sessions. 

## ✨ Key Features
- **Real-time Monitoring**: Tracks eye aspect ratio (EAR), head pose, and gaze.
- **Study Sessions**: Organize your study time and track progress.
- **Personalized Insights**: Review your focus trends with data-driven analytics.
- **AI Coach**: Optional Gemini integration for study tips and session summaries.
- **Privacy Focused**: All biometric processing happens locally on your computer.

## 🛠️ Setup Instructions

### 1. Installation
```bash
# Create environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Running the App
```bash
streamlit run app.py
```

### 3. Hosting & Deployment
This app is ready for deployment on multiple platforms:

#### 🟢 Option A: Streamlit Community Cloud (Recommended)
1. Push your code to a **GitHub** repository.
2. Sign in to [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository and click **Deploy**.

#### 🔥 Option B: Render (Docker-based)
1. Connect your repository to [Render.com](https://render.com).
2. Choose **Web Service** → Create from **Blueprint**.
3. Render will use the `render.yaml` and `Dockerfile` automatically.
4. Add your `GOOGLE_API_KEY` (Gemini) in the Render dashboard's **Environment Variables**.

#### 🤗 Option C: Hugging Face Spaces
1. Create a new **Space** on [huggingface.co/spaces](https://huggingface.co/spaces).
2. Select **Streamlit** as the SDK.
3. Upload your files or connect via Git.
4. Hugging Face will use `requirements.txt` and `packages.txt` to install all vision dependencies.

#### 🚆 Option D: Railway
1. Create a new project on [Railway.app](https://railway.app).
2. "Deploy from GitHub repo".
3. Railway will pick up the `Dockerfile` and start the service.

---

### 🔑 Authentication & Secrets
- **Gemini AI**: To enable the **AI Coach**, you MUST set an environment variable named `GOOGLE_API_KEY`.
- **Database**: By default, the app uses a local `focus_flow.db` (SQLite). For production, you can set a `DATABASE_URL` pointing to a PostgreSQL or Supabase instance.

## 🔐 Privacy & Authentication
- **Local Storage**: Data is saved to a local `focus_flow.db` file.
- **User Accounts**: Create your own private account using the "Register" tab on the landing page.
- **Default Login**: For testing, you can use `admin` / `admin123`.

---
*Created by SADANAND*
