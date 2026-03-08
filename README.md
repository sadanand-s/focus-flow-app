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

### 3. Hosting (Optional)
This app is ready for deployment on Streamlit Cloud. Simply push to your GitHub and connect it to [share.streamlit.io](https://share.streamlit.io).

## 🔐 Privacy & Authentication
- **Local Storage**: Data is saved to a local `focus_flow.db` file.
- **User Accounts**: Create your own private account using the "Register" tab on the landing page.
- **Default Login**: For testing, you can use `admin` / `admin123`.

---
*Created by SADANAND*
