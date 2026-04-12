import json
import time
from concurrent.futures import ThreadPoolExecutor

BRIDGE_DIR = "/tmp/llm_bridge"

BRIDGE_SETUP_CODE = f"""
    import json, time, os, uuid

    os.makedirs("{BRIDGE_DIR}/requests", exist_ok=True)
    os.makedirs("{BRIDGE_DIR}/responses", exist_ok=True)

    def llm_call(prompt, timeout=120):
        req_id = str(uuid.uuid4())
        req_path = f"{BRIDGE_DIR}/requests/{{req_id}}.json"
        resp_path = f"{BRIDGE_DIR}/responses/{{req_id}}.json"

        with open(req_path, "w") as f:
            json.dump({{"prompt": str(prompt)}}, f)

        start = time.time()
        while not os.path.exists(resp_path):
            if time.time() - start > timeout:
                return f"ERROR: llm_call timed out after {{timeout}}s"
            time.sleep(0.2)

        with open(resp_path) as f:
            return json.load(f)["response"]
    """


def _service_request(sandbox, req_name, on_request):
    """Service one file-based IPC request between sandbox and host."""
    req_path = f"{BRIDGE_DIR}/requests/{req_name}"
    raw = sandbox.files.read(req_path)
    content = raw.decode() if isinstance(raw, bytes) else raw
    prompt = json.loads(content)["prompt"]

    response_text = on_request(prompt)

    req_id = req_name.replace(".json", "")
    resp_path = f"{BRIDGE_DIR}/responses/{req_id}.json"
    sandbox.files.write(resp_path, json.dumps({"response": response_text}).encode())


def execute_with_bridge(sandbox, code, on_request):
    """Run sandbox code while servicing llm_call() requests from the host side."""
    watcher = sandbox.files.watch_dir(f"{BRIDGE_DIR}/requests/")

    # run_code blocks, so it runs in a thread while polling for bridge requests
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(sandbox.run_code, code)

        processed = set()
        while not future.done():
            for event in watcher.get_new_events():
                if event.name.endswith(".json") and event.name not in processed:
                    processed.add(event.name)
                    _service_request(sandbox, event.name, on_request)
            time.sleep(0.1)

        watcher.stop()
        return future.result()
