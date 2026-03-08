"""
gemini_utils.py — Google Gemini AI integration for session reports, real-time suggestions, and the AI Coach.
Includes multi-turn conversation support and context-aware coaching.
"""
import google.generativeai as genai
import time
import os
import streamlit as st

def _get_api_key(passed_key: str = None) -> str:
    """Helper to get API key from various sources (Arg > Secrets > Env)."""
    if passed_key: return passed_key
    # Try Streamlit Secrets
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception: pass
    # Try OS Env
    return os.getenv("GEMINI_API_KEY", "")

def generate_session_summary(api_key: str, session_stats: dict) -> str:
    """Generate a comprehensive session summary using Gemini AI."""
    api_key = _get_api_key(api_key)
    if not api_key: return _template_summary(session_stats)
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""Analyze this study session for a student:
        Session: {session_stats.get('name')} | Duration: {session_stats.get('duration')} min | Tag: {session_stats.get('tag')}
        Avg Engagement: {session_stats.get('avg_engagement')}% | Peak: {session_stats.get('peak_engagement')}% | Distractions: {session_stats.get('distractions')}
        Avg EAR: {session_stats.get('avg_ear')} | Gaze: {session_stats.get('avg_gaze')} | Spoof: {session_stats.get('spoof_detected')}
        
        Provide: 1. Summary (2-3 sentences), 2. Strengths, 3. Areas for improvement, 4. 2-3 Actionable tips, 5. Motivational closing.
        Friendly, warm tone."""
        return model.generate_content(prompt).text
    except Exception as e:
        return f"⚠️ AI Error: {str(e)}\n\n{_template_summary(session_stats)}"

def generate_realtime_suggestion(api_key: str, context: dict) -> str:
    """Generate a brief real-time refocus nudge."""
    api_key = _get_api_key(api_key)
    if not api_key: return _template_suggestion(context)
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Student distracted for {context.get('distraction_minutes')}m. Session: {context.get('subject')}, {context.get('engagement')}% focus. ONE brief friendly refocus tip (1-2 sentences) + emoji."
        return model.generate_content(prompt).text.strip()
    except Exception: return _template_suggestion(context)

def generate_coach_response(api_key: str, user_query: str, chat_history: list, context: dict) -> str:
    """
    Generate a conversational response from the AI Coach.
    Context includes: last 30 days session summaries, current session stats, user preferences.
    """
    api_key = _get_api_key(api_key)
    if not api_key: 
        return "🤖 **AI Coach (Demo Mode):** I need a Gemini API key in Settings to give personalized insights! Based on your query, focus on consistency. 💡 Try the Pomodoro technique!"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        system_context = f"""You are 'Focus Flow AI Coach', a warm and encouraging study partner.
        User Context:
        - Recent patterns: {context.get('history_summary', 'No recent sessions found')}
        - Current Session: {context.get('current_session', 'None active')}
        - User Preferences: Focus {context.get('thresholds', '70/40')}
        - Time: {time.strftime('%H:%M')}
        
        Rules:
        1. Be conversational, warm, and data-driven.
        2. Use the numbers from the context.
        3. End with 1-2 actionable tips.
        4. If they ask about patterns, explain when they focus best.
        """
        
        # Format chat history for Gemini
        messages = [{"role": "user" if m["is_user"] else "model", "parts": [m["text"]]} for m in chat_history]
        # Prepend system context to the current query for now (or use chat session)
        full_query = f"[SYSTEM CONTEXT: {system_context}] User asks: {user_query}"
        
        response = model.generate_content(full_query)
        return response.text
    except Exception as e:
        return f"🤖 **AI Coach:** I'm having trouble connecting right now ({str(e)}). But keep going! Persistence is key. 💪"

def _template_summary(stats: dict) -> str:
    avg = stats.get('avg_engagement', 0)
    feedback = "Outstanding focus!" if avg >= 80 else "Solid performance!" if avg >= 60 else "Moderate focus."
    return f"## Session Report\n**Avg Engagement:** {avg:.1f}%\n{feedback}\n\n*Demo template summary (No API Key)*"

def _template_suggestion(context: dict) -> str:
    return "🧘 Take a deep breath and return to your material. You've got this!"
