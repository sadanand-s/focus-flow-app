"""
gemini_utils.py — Google Gemini AI integration for session reports and real-time suggestions.
Falls back to template-based reports when no API key is provided.
"""
import google.generativeai as genai


def generate_session_summary(api_key: str, session_stats: dict) -> str:
    """
    Generate a comprehensive session summary using Gemini AI.
    Falls back to template if no API key.
    """
    if not api_key:
        return _template_summary(session_stats)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""You are an AI study coach analyzing a student's study engagement session.
Here are the detailed stats:

📊 Session Overview:
- Session Name: {session_stats.get('name', 'Study Session')}
- Duration: {session_stats.get('duration', 'N/A')} minutes
- Subject/Tag: {session_stats.get('tag', 'General')}

📈 Engagement Metrics:
- Average Engagement Score: {session_stats.get('avg_engagement', 'N/A')}/100
- Peak Engagement: {session_stats.get('peak_engagement', 'N/A')}/100
- Total Distraction Events: {session_stats.get('distractions', 'N/A')}
- Time Focused: {session_stats.get('focus_percentage', 'N/A')}%

👁️ Eye & Attention Metrics:
- Average EAR (Eye Aspect Ratio): {session_stats.get('avg_ear', 'N/A')}
- Average Gaze Score: {session_stats.get('avg_gaze', 'N/A')}/1.0
- Drowsiness Episodes: {session_stats.get('drowsy_episodes', 0)}

⚠️ Alerts:
- Spoof/Static Image Detected: {session_stats.get('spoof_detected', False)}

Please provide:
1. A brief encouraging summary of their performance (2-3 sentences)
2. Key strengths observed
3. Areas for improvement
4. 2-3 specific, actionable tips for their next session
5. A motivational closing line

Keep the tone friendly, supportive, and constructive. Use emojis sparingly for warmth.
Format with clear sections using headers."""

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"⚠️ AI summary generation failed: {str(e)}\n\n{_template_summary(session_stats)}"


def generate_realtime_suggestion(api_key: str, context: dict) -> str:
    """
    Generate a brief real-time suggestion based on current engagement state.
    Returns a short actionable message.
    """
    if not api_key:
        return _template_suggestion(context)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""You are a helpful AI study coach. The student has been distracted
for {context.get('distraction_minutes', 0)} minutes during their study session.

Current state:
- Current engagement: {context.get('engagement', 0)}%
- Session duration so far: {context.get('session_minutes', 0)} minutes
- Subject: {context.get('subject', 'General')}
- Total distractions today: {context.get('total_distractions', 0)}

Give ONE brief, friendly suggestion (1-2 sentences max) to help them refocus.
Be specific and actionable. Include an emoji. Don't be preachy."""

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception:
        return _template_suggestion(context)


def _template_summary(stats: dict) -> str:
    """Template-based summary when no Gemini API key is available."""
    avg = stats.get('avg_engagement', 0)
    duration = stats.get('duration', 0)
    distractions = stats.get('distractions', 0)
    name = stats.get('name', 'Study Session')

    # Performance assessment
    if avg >= 80:
        grade = "Excellent"
        emoji = "🌟"
        feedback = "Outstanding focus! You maintained exceptional concentration throughout."
    elif avg >= 60:
        grade = "Good"
        emoji = "👍"
        feedback = "Solid performance! Your focus was generally strong with some room for improvement."
    elif avg >= 40:
        grade = "Fair"
        emoji = "📊"
        feedback = "You showed moderate focus. Consider breaking your sessions into smaller intervals."
    else:
        grade = "Needs Improvement"
        emoji = "💪"
        feedback = "This session was challenging. Don't worry — focus is a skill that improves with practice!"

    summary = f"""## {emoji} Session Report: {name}

### Performance: {grade}
{feedback}

### 📊 Key Stats
- **Duration**: {duration:.1f} minutes
- **Average Engagement**: {avg:.1f}%
- **Total Distractions**: {distractions}

### 💡 Tips for Next Session
1. {"Try the Pomodoro technique: 25 min focus, 5 min break" if avg < 60 else "Keep up your current routine!"}
2. {"Minimize phone distractions by keeping it in another room" if distractions > 5 else "Your distraction management is solid"}
3. {"Stay hydrated and take short breaks to maintain alertness" if stats.get('avg_ear', 0.3) < 0.25 else "Your alertness levels look good"}

### 🎯 Goal for Next Session
{"Aim for 70%+ engagement and fewer than 5 distractions" if avg < 70 else "Maintain your excellent focus level!"}

---
*Report generated without AI (no Gemini API key configured)*
"""
    return summary


def _template_suggestion(context: dict) -> str:
    """Template suggestion when no API key is available."""
    minutes = context.get('distraction_minutes', 0)
    if minutes >= 5:
        return "🧘 You've been away for a while. Try a 2-minute stretch, then come back refreshed!"
    elif minutes >= 3:
        return "⏰ 3 minutes off-task! Try closing other tabs and taking a deep breath."
    else:
        return "👀 Quick check-in: refocus on your material. You've got this!"
