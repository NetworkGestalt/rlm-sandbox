import argparse
import asyncio
import json
import threading
import webbrowser
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sandbox.manager import create_sandbox
from agent.orchestrator import initialize_repl, run, Interrupted
from config import LLM_MODEL, DEFAULT_DIRECTORY, DEFAULT_TASK

UI_DIR = Path(__file__).parent

app = FastAPI()

app.mount("/static", StaticFiles(directory=UI_DIR), name="static")


@app.get("/")
async def index():
    """Serve the single-page UI."""
    return FileResponse(UI_DIR / "index.html")


@app.get("/defaults")
async def defaults():
    """Return default task and directory for the UI to pre-fill."""
    return {
        "task": DEFAULT_TASK,
        "directory": str(DEFAULT_DIRECTORY.resolve()),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Accept a task, run the agent in a thread, and stream events back."""
    await websocket.accept()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    cancel = threading.Event()

    try:
        raw = await websocket.receive_text()
        msg = json.loads(raw)
        task = msg["task"]
        directory = Path(msg["directory"])
    except (WebSocketDisconnect, KeyError):
        return

    def on_event(event):
        """Thread-safe callback: push events from the agent thread into the async queue."""
        loop.call_soon_threadsafe(queue.put_nowait, event)

    def run_agent():
        """Create sandbox, initialize REPL, and run the agent loop."""
        on_event({"type": "status", "message": "Creating sandbox..."})
        sandbox = create_sandbox(directory)
        try:
            on_event({"type": "status", "message": "Initializing REPL..."})
            metadata = initialize_repl(sandbox, task)
            on_event({"type": "init", "metadata": metadata})
            on_event({"type": "status", "message": f"Agent running... ({LLM_MODEL})"})
            result = run(task, sandbox, metadata, on_event=on_event, cancel=cancel)
            on_event({"type": "done", "result": result})
        except Interrupted:
            on_event({"type": "interrupted"})
        except Exception as e:
            on_event({"type": "error", "message": str(e)})
        finally:
            sandbox.kill()

    thread = threading.Thread(target=run_agent, daemon=True)
    thread.start()

    try:
        while True:
            recv_task = asyncio.ensure_future(websocket.receive_text())
            queue_task = asyncio.ensure_future(queue.get())

            done, pending = await asyncio.wait(
                {recv_task, queue_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for p in pending:
                p.cancel()

            for d in done:
                if d is recv_task:
                    client_msg = json.loads(d.result())
                    if client_msg.get("type") == "interrupt":
                        cancel.set()
                elif d is queue_task:
                    event = d.result()
                    await websocket.send_json(event)
                    if event["type"] in ("done", "error", "interrupted"):
                        return
    except WebSocketDisconnect:
        cancel.set()


def main():
    """Parse CLI args, start uvicorn, and optionally open the browser."""
    parser = argparse.ArgumentParser(prog="rlm-sandbox")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open browser")
    args = parser.parse_args()

    host = "127.0.0.1"
    url = f"http://{host}:{args.port}"
    print(f"Starting server at {url}")
    if not args.no_open:
        webbrowser.open(url)
    uvicorn.run(app, host=host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
