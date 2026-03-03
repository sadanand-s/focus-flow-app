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
def _patched_get_event_loop():
    """Create and set a new event loop if none exists (Python 3.14 fix)."""
    try:
        loop = asyncio._get_running_loop()
        if loop is not None:
            return loop
    except AttributeError:
        pass
    # Create a new loop if none is running
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
    except Exception as e:
        raise RuntimeError(f'Could not create event loop: {e}')


asyncio.get_event_loop = _patched_get_event_loop

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
        "--server.enableXsrfProtection", "false",
    ]
    stcli.main()
