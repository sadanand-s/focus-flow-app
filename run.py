"""
run.py — Python 3.14-compatible launcher for Focus Flow.

Usage: python run.py

Patches the asyncio event loop issue with Python 3.14 before starting Streamlit,
since asyncio.get_event_loop() no longer auto-creates a loop in Python 3.14+.
"""
import asyncio
import sys
import os


# ─── Python 3.14 asyncio compatibility patch ─────────────────────────────────
import threading

_loop_lock = threading.Lock()

def _patched_get_event_loop():
    """Create and set a new event loop if none exists (Python 3.14 fix)."""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        with _loop_lock:
            try:
                # Double check inside lock
                return asyncio.get_event_loop_policy().get_event_loop()
            except (RuntimeError, AssertionError):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop

# Apply patches early
asyncio.get_event_loop = _patched_get_event_loop

# Also patch the default policy if it's the old one
try:
    policy = asyncio.get_event_loop_policy()
    if not hasattr(policy, '_patched'):
        old_get_loop = policy.get_event_loop
        def patched_get_loop(self):
            try:
                return old_get_loop()
            except (RuntimeError, AssertionError):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop
        policy.get_event_loop = patched_get_loop.__get__(policy, type(policy))
        policy._patched = True
except Exception:
    pass

# ─── Launch Streamlit ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    from streamlit.web import cli as stcli

    app_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(app_dir, "app.py")

    sys.argv = [
        "streamlit", "run", app_path,
        "--server.port", "8501",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.enableXsrfProtection", "true",
    ]
    stcli.main()
