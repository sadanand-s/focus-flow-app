import asyncio
import sys
import streamlit.web.bootstrap as bootstrap
import streamlit.web.cli as stcli

# Broad monkeypatch for Python 3.14+ compatibility
def get_loop_safe():
    try:
        return _old_get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

_old_get_event_loop = asyncio.get_event_loop
asyncio.get_event_loop = get_loop_safe

# Also monkeypatch the policy just in case
class SafePolicy(asyncio.DefaultEventLoopPolicy):
    def get_event_loop(self):
        return get_loop_safe()

asyncio.set_event_loop_policy(SafePolicy())

def main():
    # Prepend "run" and "app.py" to sys.argv for Streamlit CLI
    # Format: run_app.py [streamlit_args]
    # Becomes: streamlit run app.py [streamlit_args]
    original_args = sys.argv[1:]
    sys.argv = [sys.argv[0], "run", "app.py"] + original_args
    
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
