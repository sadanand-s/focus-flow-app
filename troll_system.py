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

COOLDOWN_SECONDS = 300  # 5 minutes between trolls

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
    elif troll_type == "fake_loading":
        return _fake_loading_html()
    return ""


def check_and_trigger(distraction_seconds: float, sensitivity: str = "Medium",
                      troll_mode: bool = True, nudge_only: bool = False) -> Dict[str, Any]:
    """
    Check if a troll should be triggered based on distraction duration.
    Returns: {"should_trigger": bool, "troll_type": str, "html": str, "message": str}
    """
    result: Dict[str, Any] = {
        "should_trigger": False, "troll_type": None, "html": "", "message": ""
    }

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
        msg = random.choice(SNARKY_MESSAGES)
        result["message"] = msg
        result["html"] = _snarky_toast_html(msg)
    else:
        troll_types = ["fake_popup", "emoji_storm", "snarky_toast", "red_border", "fake_loading"]
        chosen = random.choice(troll_types)
        result["troll_type"] = chosen
        if chosen == "snarky_toast":
            msg = random.choice(SNARKY_MESSAGES)
            result["message"] = msg
            result["html"] = _snarky_toast_html(msg)
        else:
            result["html"] = get_troll_html(chosen)

    return result


def get_nudge_banner_html(minutes: float) -> str:
    """Soft blue nudge banner for extended distraction."""
    return f"""
    <div style="
        background: linear-gradient(135deg, rgba(0,210,255,0.1), rgba(108,99,255,0.1));
        border: 1px solid rgba(0,210,255,0.25);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        color: white;
        display: flex;
        align-items: center;
        gap: 12px;
        animation: softPulse 2s ease-in-out infinite;
    ">
        <span style="font-size:1.5rem;">💡</span>
        <span>You've been away for <b>{minutes:.0f} minutes</b>. A 2-minute stretch might help!</span>
    </div>
    <style>
        @keyframes softPulse {{
            0%,100% {{ border-color: rgba(0,210,255,0.25); }}
            50% {{ border-color: rgba(0,210,255,0.5); }}
        }}
    </style>
    """


def get_break_modal_html() -> str:
    """5-minute break suggestion modal with breathing animation."""
    return """
    <div id="break-modal" style="
        position:fixed;top:0;left:0;width:100%;height:100%;
        background:rgba(0,0,0,0.6);z-index:99999;
        display:flex;align-items:center;justify-content:center;
        animation:fadeIn 0.3s ease;
    ">
        <div style="background:#1A1D27;border:1px solid rgba(108,99,255,0.3);
            border-radius:20px;padding:2.5rem;max-width:400px;text-align:center;color:white;
            box-shadow:0 20px 60px rgba(0,0,0,0.5);">
            <h3 style="color:#00D2FF;margin-bottom:0.5rem;">🧘 Time for a Break</h3>
            <p style="color:#9E9E9E;margin-bottom:1.5rem;">
                You've been distracted for 10 minutes.<br>Take a short breather!
            </p>

            <!-- Breathing circle animation -->
            <div style="margin:1.5rem auto;width:80px;height:80px;position:relative;">
                <div style="width:80px;height:80px;border-radius:50%;
                    background:radial-gradient(circle,rgba(108,99,255,0.4),rgba(0,210,255,0.1));
                    animation:breathe 4s ease-in-out infinite;
                    box-shadow:0 0 20px rgba(108,99,255,0.3);"></div>
            </div>
            <p style="color:#9E9E9E;font-size:0.85rem;margin-bottom:1rem;">
                Breathe in... hold... breathe out...
            </p>

            <!-- 5-min countdown -->
            <div id="break-timer" style="font-size:2rem;font-weight:800;
                font-family:'JetBrains Mono',monospace;
                background:linear-gradient(135deg,#6C63FF,#00D2FF);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                margin-bottom:1rem;">5:00</div>

            <button onclick="document.getElementById('break-modal').remove(); clearInterval(window._breakTimer);"
                style="background:linear-gradient(135deg,#6C63FF,#00D2FF);
                color:white;border:none;padding:10px 28px;border-radius:50px;
                cursor:pointer;font-weight:700;font-size:0.9rem;">
                Skip Break
            </button>
        </div>
    </div>
    <style>
        @keyframes breathe {
            0%,100% { transform: scale(0.8); opacity: 0.7; }
            50% { transform: scale(1.2); opacity: 1; }
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>
    <script>
        var secs = 300; // 5 minutes
        var el = document.getElementById('break-timer');
        window._breakTimer = setInterval(function() {
            secs--;
            if (secs <= 0) {
                clearInterval(window._breakTimer);
                var modal = document.getElementById('break-modal');
                if (modal) {
                    modal.innerHTML = '<div style="text-align:center;color:white;padding:2rem;"><div style="font-size:3rem;">💪</div><h3>Break over! Ready to get back to it?</h3><button onclick="document.getElementById(\\'break-modal\\').remove()" style="background:linear-gradient(135deg,#6C63FF,#00D2FF);color:white;border:none;padding:10px 24px;border-radius:50px;cursor:pointer;font-weight:700;margin-top:1rem;">Let\\'s Go!</button></div>';
                }
                return;
            }
            var m = Math.floor(secs / 60);
            var s = secs % 60;
            if (el) el.textContent = m + ':' + (s < 10 ? '0' : '') + s;
        }, 1000);
    </script>
    """


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
        <button onclick="document.getElementById('troll-popup').style.display='none'"
            style="background: #1a1a1a; color: #FFD700; border: none; padding: 10px 24px;
            border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 0.9rem;
            margin-right: 8px;">
            ACCEPT 🎁
        </button>
        <button onclick="document.getElementById('troll-popup').style.display='none'"
            style="background: rgba(0,0,0,0.2); color: #1a1a1a; border: none; padding: 10px 24px;
            border-radius: 10px; cursor: pointer; font-size: 0.9rem;">
            Decline
        </button>
    </div>
    <script>
        // Auto-dismiss after 8 seconds
        setTimeout(function() {
            var el = document.getElementById('troll-popup');
            if (el) el.style.display = 'none';
        }, 8000);
    </script>
    """


def _emoji_storm_html() -> str:
    emojis = "🤡💤📚🎪😴🧠🔔⏰🎯💡"
    return f"""
    <div id="emoji-storm" style="position:fixed;top:0;left:0;width:100%;height:100%;
        pointer-events:none;z-index:99998;overflow:hidden;">
        <style>
            @keyframes floatUp {{
                0% {{ transform: translateY(100vh) rotate(0deg); opacity: 1; }}
                80% {{ opacity: 1; }}
                100% {{ transform: translateY(-10vh) rotate(720deg); opacity: 0; }}
            }}
            .emoji-particle {{
                position: absolute;
                font-size: 2rem;
                animation: floatUp linear forwards;
                pointer-events: none;
            }}
        </style>
    </div>
    <script>
        (function() {{
            var container = document.getElementById('emoji-storm');
            var emojiArr = Array.from('{emojis}');
            for (var i = 0; i < 30; i++) {{
                var el = document.createElement('span');
                el.className = 'emoji-particle';
                el.textContent = emojiArr[Math.floor(Math.random() * emojiArr.length)];
                el.style.left = Math.random() * 100 + '%';
                el.style.bottom = '-50px';
                el.style.animationDuration = (2 + Math.random() * 2) + 's';
                el.style.animationDelay = Math.random() * 1.5 + 's';
                el.style.fontSize = (1.2 + Math.random() * 1.5) + 'rem';
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
        <span style="float: right; opacity: 0.7; font-size: 0.8rem; margin-left: 8px;">✕</span>
    </div>
    <script>
        setTimeout(function() {{
            var el = document.getElementById('snarky-toast');
            if (el) el.style.display = 'none';
        }}, 7000);
    </script>
    """


def _red_border_html() -> str:
    return """
    <style>
        @keyframes pulse-red-border {
            0%, 100% { box-shadow: 0 0 0 0 rgba(255,82,82,0); }
            50% { box-shadow: 0 0 0 6px rgba(255,82,82,0.4); }
        }
    </style>
    <script>
        (function() {
            var target = window.parent.document.querySelector('[data-testid="stVerticalBlock"]');
            if (!target) target = window.parent.document.querySelector('section.main');
            if (target) {
                target.style.border = '3px solid #FF5252';
                target.style.borderRadius = '12px';
                target.style.animation = 'pulse-red-border 1.2s ease-in-out 4';
                setTimeout(function() {
                    target.style.border = '';
                    target.style.borderRadius = '';
                    target.style.animation = '';
                }, 7000);
            }
        })();
    </script>
    """


def _fake_loading_html() -> str:
    return """
    <div id="fake-load" style="
        position:fixed;top:0;left:0;width:100%;height:100%;
        background:rgba(15,17,23,0.92);z-index:99999;
        display:flex;flex-direction:column;align-items:center;justify-content:center;
        font-family:'Inter',Arial,sans-serif;color:white;
        animation:fadeIn 0.3s ease;
    ">
        <style>
            @keyframes fillBar {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            @keyframes fadeIn { from{opacity:0} to{opacity:1} }
        </style>
        <div style="font-size:2rem;margin-bottom:1rem;">⚠️</div>
        <h3 style="margin-bottom:0.5rem;color:#FFD600;">Reloading your focus...</h3>
        <div style="width:300px;height:12px;background:rgba(255,255,255,0.1);
            border-radius:6px;overflow:hidden;margin:1rem 0;">
            <div id="fake-bar" style="height:100%;
                background:linear-gradient(135deg,#6C63FF,#00D2FF);
                border-radius:6px;width:0%;
                animation:fillBar 2.5s ease forwards;"></div>
        </div>
        <p id="fake-pct" style="color:#9E9E9E;font-size:0.9rem;">0%</p>
    </div>
    <script>
        var pct = 0;
        var iv = setInterval(function() {
            pct = Math.min(pct + 4, 100);
            var el = document.getElementById('fake-pct');
            if (el) el.textContent = pct + '% ████████░░░░';
        }, 100);
        setTimeout(function() {
            clearInterval(iv);
            var el = document.getElementById('fake-load');
            if (el) {
                el.innerHTML = '<div style="text-align:center"><div style="font-size:3rem">✅</div><h3 style="color:#00E676;margin:.5rem 0">Focus restored!</h3><p style="color:#9E9E9E">(Maybe.)</p></div>';
                setTimeout(function() { if(el) el.remove(); }, 2000);
            }
        }, 2800);
    </script>
    """
