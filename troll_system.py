"""
troll_system.py — Troll & Nudge engine for distraction notifications.
Max 1 troll per 5 minutes, all dismissible, supports nudge-only mode.
"""
import time
import random
from typing import Optional, Dict, Any
import streamlit as st


SNARKY_MESSAGES = [
    "Bro, your notes won't read themselves 📚",
    "Earth to student... come in, student! 🛸",
    "Your textbook misses you 💔",
    "Procrastination level: Expert 🏆",
    "Netflix can wait, your grades can't 📉",
    "Focus mode: DEACTIVATED. Engaging troll protocol... 🤖",
    "Your future self is judging you right now 👀",
    "That wall is fascinating, isn't it? Study > wall. 🧱",
    "Did you forget you started a study session? 🤔",
    "Legend says focused students get better grades... 🧙‍♂️",
]

COOLDOWN_SECONDS = 300  # 5 minutes between trolls

# Sensitivity thresholds (seconds of distraction before triggering)
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
    elif troll_type == "screen_wiggle":
        return _screen_wiggle_html()
    elif troll_type == "snarky_toast":
        return _snarky_toast_html()
    elif troll_type == "red_border":
        return _red_border_html()
    return ""


def check_and_trigger(distraction_seconds: float, sensitivity: str = "Medium",
                      troll_mode: bool = True, nudge_only: bool = False) -> Dict[str, Any]:
    """
    Check if a troll should be triggered based on distraction duration.
    Returns: {"should_trigger": bool, "troll_type": str, "html": str, "message": str}
    """
    result: Dict[str, Any] = {"should_trigger": False, "troll_type": None, "html": "", "message": ""}

    if not troll_mode:
        return result

    threshold = SENSITIVITY_MAP.get(sensitivity, 120)
    if distraction_seconds < threshold:
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
        result["troll_type"] = "snarky_toast"
        result["message"] = random.choice(SNARKY_MESSAGES)
        result["html"] = _snarky_toast_html(result["message"])
    else:
        troll_types = ["fake_popup", "emoji_storm", "screen_wiggle", "snarky_toast", "red_border"]
        chosen = random.choice(troll_types)
        result["troll_type"] = chosen
        if chosen == "snarky_toast":
            result["message"] = random.choice(SNARKY_MESSAGES)
            result["html"] = _snarky_toast_html(result["message"])
        else:
            result["html"] = get_troll_html(chosen)

    return result


def _fake_popup_html() -> str:
    return """
    <div id="troll-popup" style="
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #FFD700, #FF6B35);
        border-radius: 20px; padding: 30px 40px; z-index: 99999;
        color: #1a1a1a; text-align: center; font-family: 'Arial', sans-serif;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        max-width: 400px;
    ">
        <style>
            @keyframes popIn {
                0% { transform: translate(-50%,-50%) scale(0); opacity: 0; }
                100% { transform: translate(-50%,-50%) scale(1); opacity: 1; }
            }
            @keyframes shimmer {
                0% { background-position: -200% 0; }
                100% { background-position: 200% 0; }
            }
        </style>
        <div style="font-size: 3rem; margin-bottom: 10px;">🎉🎊🏆</div>
        <h2 style="margin: 0 0 8px 0; font-size: 1.4rem;">CONGRATULATIONS!</h2>
        <p style="margin: 0 0 15px 0; font-size: 1rem; opacity: 0.85;">
            You've won a <b>FREE NAP!</b><br>
            <span style="font-size: 0.8rem;">(Just kidding. Get back to studying!)</span>
        </p>
        <button onclick="document.getElementById('troll-popup').style.display='none'"
            style="background: #1a1a1a; color: #FFD700; border: none; padding: 10px 24px;
            border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 0.9rem;">
            😤 Fine, I'll study
        </button>
    </div>
    """


def _emoji_storm_html() -> str:
    emojis = "🎪🤡💤😴📚🧠⏰🔔"
    return f"""
    <div id="emoji-storm" style="position:fixed;top:0;left:0;width:100%;height:100%;
        pointer-events:none;z-index:99998;overflow:hidden;">
        <style>
            @keyframes fall {{
                0% {{ transform: translateY(-50px) rotate(0deg); opacity: 1; }}
                100% {{ transform: translateY(100vh) rotate(720deg); opacity: 0; }}
            }}
            .emoji-particle {{
                position: absolute;
                font-size: 2rem;
                animation: fall linear forwards;
                pointer-events: none;
            }}
        </style>
    </div>
    <script>
        (function() {{
            const container = document.getElementById('emoji-storm');
            const emojis = '{emojis}'.split('');
            // Using Array.from to handle multi-byte emoji
            const emojiArr = Array.from(emojis.join(''));
            for (let i = 0; i < 40; i++) {{
                const el = document.createElement('span');
                el.className = 'emoji-particle';
                el.textContent = emojiArr[Math.floor(Math.random() * emojiArr.length)] || '🤡';
                el.style.left = Math.random() * 100 + '%';
                el.style.animationDuration = (1.5 + Math.random() * 2) + 's';
                el.style.animationDelay = Math.random() * 0.8 + 's';
                el.style.fontSize = (1.2 + Math.random() * 1.5) + 'rem';
                container.appendChild(el);
            }}
            setTimeout(() => {{ if(container) container.remove(); }}, 4000);
        }})();
    </script>
    """


def _screen_wiggle_html() -> str:
    return """
    <style>
        @keyframes wiggle {
            0%, 100% { transform: translateX(0); }
            10% { transform: translateX(-5px) rotate(-0.5deg); }
            20% { transform: translateX(5px) rotate(0.5deg); }
            30% { transform: translateX(-4px) rotate(-0.3deg); }
            40% { transform: translateX(4px) rotate(0.3deg); }
            50% { transform: translateX(-3px); }
            60% { transform: translateX(3px); }
            70% { transform: translateX(-2px); }
            80% { transform: translateX(2px); }
            90% { transform: translateX(-1px); }
        }
    </style>
    <script>
        (function() {
            const main = window.parent.document.querySelector('section.main');
            if (main) {
                main.style.animation = 'wiggle 0.5s ease-in-out 3';
                setTimeout(() => { main.style.animation = ''; }, 2000);
            }
        })();
    </script>
    """


def _snarky_toast_html(message: Optional[str] = None) -> str:
    if not message:
        message = random.choice(SNARKY_MESSAGES)
    return f"""
    <div id="snarky-toast" style="
        position: fixed; bottom: 30px; right: 30px; z-index: 99999;
        background: linear-gradient(135deg, #FF4B4B, #FF6B6B);
        color: white; padding: 16px 24px; border-radius: 14px;
        font-family: 'Arial', sans-serif; font-size: 0.95rem;
        box-shadow: 0 8px 32px rgba(255,75,75,0.4);
        animation: slideIn 0.4s ease-out;
        max-width: 350px; cursor: pointer;
    " onclick="this.style.display='none'">
        <style>
            @keyframes slideIn {{
                0% {{ transform: translateX(120%); opacity: 0; }}
                100% {{ transform: translateX(0); opacity: 1; }}
            }}
        </style>
        <span style="font-size: 1.2rem; margin-right: 8px;">🤡</span>
        {message}
        <span style="float: right; opacity: 0.7; font-size: 0.8rem;">✕</span>
    </div>
    <script>
        setTimeout(() => {{
            const el = document.getElementById('snarky-toast');
            if (el) el.style.display = 'none';
        }}, 6000);
    </script>
    """


def _red_border_html() -> str:
    return """
    <style>
        @keyframes pulse-border {
            0%, 100% { box-shadow: 0 0 0 0 rgba(255,75,75,0); }
            50% { box-shadow: 0 0 0 6px rgba(255,75,75,0.5); }
        }
    </style>
    <script>
        (function() {
            const main = window.parent.document.querySelector('section.main');
            if (main) {
                main.style.border = '3px solid #FF4B4B';
                main.style.borderRadius = '10px';
                main.style.animation = 'pulse-border 1s ease-in-out 5';
                setTimeout(() => {
                    main.style.border = '';
                    main.style.borderRadius = '';
                    main.style.animation = '';
                }, 6000);
            }
        })();
    </script>
    """
