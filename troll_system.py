"""
troll_system.py — The legendary Troll & Nudge engine.
Keeping students on their toes with snarky reminders and chaos.
"""
import time
import random
from typing import Optional, Dict, Any
import streamlit as st

# The snarky personality is back!
SNARKY_MESSAGES = [
    "Bro, your notes won't read themselves 📚",
    "The WiFi is probably more focused than you rn 😐",
    "Your future self called. They said get back to work.",
    "Even your screen is bored watching you be distracted.",
    "🚨 DISTRACTION ALERT: You, right now.",
    "Earth to student... come in, student! 🛸",
    "Your textbook misses you 💔",
    "Procrastination level: Expert 🏆",
    "Netflix can wait, your grades can't 📉",
    "Your future self is judging you right now 👀",
    "Legend says focused students get better grades... 🧙‍♂️",
]

COOLDOWN_SECONDS = 3  # 3 seconds between active trolls

SENSITIVITY_MAP = {
    "Low": 180,     # 3 minutes
    "Medium": 120,  # 2 minutes
    "High": 60,     # 1 minute
}

def get_troll_html(troll_type: str) -> str:
    """Return HTML/JS string for the given troll effect."""
    if troll_type == "fake_popup":
        return _fake_popup_html()
    elif troll_type == "emoji_storm":
        return _emoji_storm_html()
    elif troll_type == "snarky_toast":
        return _snarky_toast_html()
    elif troll_type == "red_border":
        return _red_border_html()
    return ""

def check_and_trigger(distraction_seconds: float, 
                      engagement_score: Optional[float] = None,
                      sensitivity: str = "Medium",
                      troll_mode: bool = True, 
                      nudge_only: bool = False) -> Dict[str, Any]:
    """
    Check if a troll should be triggered based on distraction duration OR low engagement.
    """
    result: Dict[str, Any] = {
        "should_trigger": False, "troll_type": None, "html": "", "message": ""
    }

    if not troll_mode:
        return result

    # ─── Threshold Logic ───
    threshold = SENSITIVITY_MAP.get(sensitivity, 120)
    score_trigger = False
    
    if engagement_score is not None:
        if engagement_score < 45 and distraction_seconds > 2:
            score_trigger = True
        elif engagement_score < 65 and distraction_seconds > (threshold / 3):
            score_trigger = True

    time_trigger = distraction_seconds >= threshold

    if not (time_trigger or score_trigger):
        return result

    # Check cooldown
    last_troll = st.session_state.get("last_troll_time", 0)
    now = time.time()
    if now - last_troll < COOLDOWN_SECONDS:
        return result

    # Trigger!
    result["should_trigger"] = True
    st.session_state["last_troll_time"] = now

    if nudge_only:
        msg = random.choice(SNARKY_MESSAGES)
        result["troll_type"] = "snarky_toast"
        result["message"] = msg
        result["html"] = _snarky_toast_html(msg)
    else:
        troll_types = ["fake_popup", "emoji_storm", "snarky_toast", "red_border"]
        chosen = random.choice(troll_types)
        result["troll_type"] = chosen
        if chosen == "snarky_toast":
            msg = random.choice(SNARKY_MESSAGES)
            result["message"] = msg
            result["html"] = _snarky_toast_html(msg)
        else:
            result["html"] = get_troll_html(chosen)

    return result

def _fake_popup_html() -> str:
    return """
    <div id="troll-popup" style="
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #FFD700, #FF6B35);
        border-radius: 20px; padding: 30px 40px; z-index: 99999;
        color: #1a1a1a; text-align: center; font-family: 'Inter', Arial, sans-serif;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        max-width: 400px; width: 90%;
    ">
        <style>
            @keyframes popIn {
                0% { transform: translate(-50%,-50%) scale(0.5); opacity: 0; }
                100% { transform: translate(-50%,-50%) scale(1); opacity: 1; }
            }
        </style>
        <div style="font-size: 3rem; margin-bottom: 10px;">🎉🎊🏆</div>
        <h2 style="margin: 0 0 8px 0; font-size: 1.4rem;">CONGRATULATIONS!</h2>
        <p style="margin: 0 0 15px 0; font-size: 1rem; opacity: 0.85;">
            You've been selected for a <b>FREE NAP!</b><br>
            <span style="font-size: 0.8rem;">Click ACCEPT to claim your reward.</span>
        </p>
        <button onclick="document.getElementById('troll-popup').remove()"
            style="background: #1a1a1a; color: #FFD700; border: none; padding: 10px 24px;
            border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 0.9rem;">
            ACCEPT 🎁
        </button>
    </div>
    """

def _emoji_storm_html() -> str:
    emojis = "🤡💤📚😴🧠🔔⏰🎯"
    return f"""
    <div id="emoji-storm" style="position:fixed;top:0;left:0;width:100%;height:100%;
        pointer-events:none;z-index:99998;overflow:hidden;">
        <style>
            @keyframes floatUp {{
                0% {{ transform: translateY(100vh) rotate(0deg); opacity: 1; }}
                100% {{ transform: translateY(-10vh) rotate(720deg); opacity: 0; }}
            }}
            .emoji-particle {{
                position: absolute;
                font-size: 2rem;
                animation: floatUp 3s linear forwards;
            }}
        </style>
    </div>
    <script>
        (function() {{
            var container = document.getElementById('emoji-storm');
            var emojiArr = Array.from('{emojis}');
            for (var i = 0; i < 20; i++) {{
                var el = document.createElement('span');
                el.className = 'emoji-particle';
                el.textContent = emojiArr[Math.floor(Math.random() * emojiArr.length)];
                el.style.left = Math.random() * 100 + '%';
                el.style.bottom = '-50px';
                el.style.animationDelay = Math.random() * 2 + 's';
                container.appendChild(el);
            }}
            setTimeout(function() {{ if(container) container.remove(); }}, 5000);
        }})();
    </script>
    """

def _snarky_toast_html(message: Optional[str] = None) -> str:
    if not message:
        message = random.choice(SNARKY_MESSAGES)
    return f"""
    <div id="snarky-toast" style="
        position: fixed; bottom: 30px; right: 30px; z-index: 99999;
        background: linear-gradient(135deg, #6C63FF, #00D2FF);
        color: white; padding: 16px 24px; border-radius: 14px;
        font-family: 'Inter', Arial, sans-serif; font-size: 0.95rem;
        box-shadow: 0 8px 32px rgba(108,99,255,0.4);
        animation: slideIn 0.4s ease-out;
        max-width: 350px; display: flex; align-items: center; gap: 12px;
    ">
        <style>
            @keyframes slideIn {{
                0% {{ transform: translateX(120%); opacity: 0; }}
                100% {{ transform: translateX(0); opacity: 1; }}
            }}
        </style>
        <span style="font-size: 1.2rem;">🤡</span>
        <div>{message}</div>
        <button onclick="this.parentElement.remove()" style="background:none; border:none; color:white; cursor:pointer; font-weight:bold; margin-left:auto;">✕</button>
    </div>
    <script>
        setTimeout(function() {{
            var el = document.getElementById('snarky-toast');
            if (el) el.remove();
        }}, 6000);
    </script>
    """

def _red_border_html() -> str:
    return """
    <div id="troll-border" style="
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        border: 10px solid #FF5252; pointer-events: none; z-index: 99999;
        animation: blink 0.5s step-end infinite;
    "></div>
    <style>
        @keyframes blink { 
            50% { opacity: 0; } 
        }
    </style>
    <script>
        setTimeout(function() {
            var el = document.getElementById('troll-border');
            if (el) el.remove();
        }, 5000);
    </script>
    """

# Naming compatibility
def get_nudge_html(nudge_type: str) -> str:
    return get_troll_html(nudge_type)
