import threading
import time

from e2b_code_interpreter import Sandbox

from config import SANDBOX_TEMPLATE

POLL_CODE = """
import os, time

start = time.time()
while not os.path.exists("/tmp/bridge_test.txt"):
    if time.time() - start > 30:
        print("TIMEOUT: file never appeared")
        break
    time.sleep(0.1)
else:
    with open("/tmp/bridge_test.txt") as f:
        print(f"GOT: {f.read()}")
"""


if __name__ == "__main__":
    # Validates that sandbox.files.write() works while run_code() is blocking in another thread
    sandbox = Sandbox.create(template=SANDBOX_TEMPLATE, timeout=60)
    print(f"Sandbox created: {sandbox.sandbox_id}")

    result = [None]

    def run_in_thread():
        result[0] = sandbox.run_code(POLL_CODE)

    thread = threading.Thread(target=run_in_thread)
    thread.start()

    time.sleep(2)
    print("Writing file from main thread...")
    sandbox.files.write("/tmp/bridge_test.txt", b"hello from the host")

    thread.join(timeout=35)

    if result[0]:
        stdout = "".join(result[0].logs.stdout)
        stderr = "".join(result[0].logs.stderr)
        print(f"stdout: {stdout}")
        if stderr:
            print(f"stderr: {stderr}")
        if result[0].error:
            print(f"error: {result[0].error.name}: {result[0].error.value}")
    else:
        print("ERROR: run_code never returned")

    sandbox.kill()
    print("Done.")
