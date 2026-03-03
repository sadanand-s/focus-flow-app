import asyncio
import os
import sys
from streamlit.web import bootstrap
from streamlit.web.server import Server

def run_app(main_script_path):
    sys.path.insert(0, os.getcwd())
    bootstrap._fix_sys_path(main_script_path)
    bootstrap._fix_tornado_crash()
    bootstrap._fix_sys_argv(main_script_path, [])
    
    server = Server(main_script_path, False)

    async def main():
        await server.start()
        print(f"Streamlit server started: http://localhost:8501")
        await server.stopped

    try:
        asyncio.run(main())
    except RuntimeError:
        # If loop is already running, use it
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(main())
        else:
            loop.run_until_complete(main())

if __name__ == "__main__":
    run_app("app.py")
