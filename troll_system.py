"""
troll_system.py — Premium Troll & Nudge engine for stay-on-track notifications.
Includes 5 premium troll events, cooldowns, and nudge-only mode.
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
    "Netflix can wait, your grades can't 📉",
    "Focus mode: DEACTIVATED. Engaging troll protocol... 🤖",
    "Your future self is judging you right now 👀",
    "Legend says focused students get better grades... 🧙‍♂️",
]

COOLDOWN_SECONDS = 300  # Hard limit: max 1 troll per 5 minutes

def get_troll_html(troll_type: str) -> str:
    """Return HTML/JS string for the given premium troll effect."""
    if troll_type == "fake_ad":
        return _fake_ad_html()
    elif troll_type == "emoji_storm":
        return _emoji_storm_html()
    elif troll_type == "pulsing_border":
        return _pulsing_border_html()
    elif troll_type == "fake_loading":
        return _fake_loading_html()
    elif troll_type == "snarky_toast":
        return _snarky_toast_html()
    return ""

def check_and_trigger(distraction_seconds: float) -> Optional[Dict[str, Any]]:
    """
    Check if a troll should be triggered based on distraction duration.
    Trigger if distracted for > 2 consecutive minutes.
    """
    config = st.session_state.get('settings_config', {})
    if not st.session_state.get("troll_mode", True):
        return None

    # Nudge Only mode check
    nudge_only = st.session_state.get("nudge_only", False)

    # Threshold: default 2 minutes (120s)
    threshold = config.get("distracted_threshold", 40) # This is percentage... 
    # Wait, the prompt said "distracted for more than 2 consecutive minutes".
    # I'll use a hardcoded 120s or check a specific setting if I add one.
    
    if distraction_seconds < 120:
        return None

    # Check cooldown
    last_troll = st.session_state.get("last_troll_time", 0)
    now = time.time()
    if now - last_troll < COOLDOWN_SECONDS:
        return None

    # Trigger!
    st.session_state["last_troll_time"] = now
    
    result = {"should_trigger": True}
    
    if nudge_only:
        chosen = "snarky_toast"
    else:
        troll_types = ["fake_ad", "emoji_storm", "pulsing_border", "fake_loading", "snarky_toast"]
        chosen = random.choice(troll_types)
    
    result["troll_type"] = chosen
    result["html"] = get_troll_html(chosen)
    if chosen == "snarky_toast":
        result["message"] = random.choice(SNARKY_MESSAGES)
        result["html"] = _snarky_toast_html(result["message"])
        
    return result

def _fake_ad_html() -> str:
    return """
    <div id="troll-ad" style="
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        background: #1A1D27; border: 1px solid #6C63FF;
        border-radius: 20px; padding: 40px; z-index: 99999;
        color: white; text-align: center; font-family: 'Inter', sans-serif;
        box-shadow: 0 20px 60px rgba(0,0,0,0.8);
        animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    ">
        <h2 style="margin: 0; color: #6C63FF;">🎉 CONGRATULATIONS!</h2>
        <p style="margin: 15px 0;">You've been selected for a <b>FREE nap!</b><br>Click ACCEPT to claim your reward.</p>
        <button onclick="childToast()" style="background: linear-gradient(135deg, #6C63FF, #00D2FF); border: none; padding: 12px 30px; border-radius: 50px; color: white; font-weight: bold; cursor: pointer;">ACCEPT</button>
        <div style="margin-top: 15px; font-size: 0.7rem; opacity: 0.5; cursor: pointer;" onclick="this.parentElement.remove()">Dismiss (Esc)</div>
    </div>
    <script>
        function childToast() {
            alert("Just kidding 😅 Get back to work!");
            document.getElementById('troll-ad').remove();
        }
        document.addEventListener('keydown', e => { if(e.key==='Escape') document.getElementById('troll-ad')?.remove(); });
    </script>
    <style>@keyframes popIn { 0% { opacity: 0; transform: translate(-50%, -50%) scale(0.5); } 100% { opacity: 1; transform: translate(-50%, -50%) scale(1); } }</style>
    """

def _emoji_storm_html() -> str:
    return """
    <div id="emoji-storm" style="position:fixed; bottom:0; left:0; width:100%; height:100%; pointer-events:none; z-index:99998; overflow:hidden;"></div>
    <script>
        (function() {
            const container = document.getElementById('emoji-storm');
            const emojis = ['🤡', '💤', '📚', '🎪', '😴', '🧠'];
            for (let i = 0; i < 30; i++) {
                const el = document.createElement('span');
                el.textContent = emojis[Math.floor(Math.random() * emojis.length)];
                el.style.position = 'absolute';
                el.style.bottom = '-50px';
                el.style.left = Math.random() * 100 + '%';
                el.style.fontSize = (Math.random() * 2 + 1) + 'rem';
                el.style.transition = 'all 3s ease-out';
                el.style.opacity = '1';
                container.appendChild(el);
                setTimeout(() => {
                    el.style.transform = `translateY(-${window.innerHeight + 100}px) rotate(${Math.random() * 360}deg)`;
                    el.style.opacity = '0';
                }, 10);
            }
            setTimeout(() => container.remove(), 3500);
        })();
    </script>
    """

def _pulsing_border_html() -> str:
    return """
    <script>
        (function() {
            const feed = window.parent.document.querySelector('[data-testid="stWebcam"]');
            if (feed) {
                feed.style.transition = 'box-shadow 0.5s';
                feed.style.animation = 'pulseRed 1s infinite';
                setTimeout(() => { feed.style.animation = ''; }, 10000);
            }
        })();
    </script>
    <style>@keyframes pulseRed { 0% { box-shadow: 0 0 0 0 rgba(255, 82, 82, 0.7); } 70% { box-shadow: 0 0 0 20px rgba(255, 82, 82, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 82, 82, 0); } }</style>
    """

def _fake_loading_html() -> str:
    return """
    <div id="fake-loader" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(15, 17, 23, 0.9); z-index: 99999; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; font-family: 'Inter', sans-serif;">
        <h2 style="color: #FFD600;">⚠️ Reloading your focus...</h2>
        <div style="width: 300px; height: 10px; background: #333; border-radius: 5px; margin: 20px 0; overflow: hidden;">
            <div id="bar" style="width: 0%; height: 100%; background: #6C63FF; transition: width 2s linear;"></div>
        </div>
        <p id="percent">0%</p>
    </div>
    <script>
        const bar = document.getElementById('bar');
        const pct = document.getElementById('percent');
        setTimeout(() => { bar.style.width = '100%'; }, 10);
        let p = 0;
        const iv = setInterval(() => {
            p += 2;
            pct.textContent = p + '%';
            if(p >= 100) clearInterval(iv);
        }, 40);
        setTimeout(() => {
            document.getElementById('fake-loader').remove();
            alert("Focus restored! (Maybe.)");
        }, 2200);
    </script>
    """

def _snarky_toast_html(message: str = "Stay focused!") -> str:
    return f"""
    <div id="snarky-toast" style="position: fixed; bottom: 30px; right: 30px; background: #FF5252; color: white; padding: 15px 25px; border-radius: 12px; z-index: 99999; box-shadow: 0 10px 30px rgba(0,0,0,0.5); font-family: sans-serif; cursor: pointer; animation: slideIn 0.3s forwards;" onclick="this.remove()">
        <b>🤡 {message}</b>
    </div>
    <style>@keyframes slideIn {{ from {{ transform: translateX(100%); }} to {{ transform: translateX(0); }} }}</style>
    <script>setTimeout(() => document.getElementById('snarky-toast')?.remove(), 5000);</script>
    """
