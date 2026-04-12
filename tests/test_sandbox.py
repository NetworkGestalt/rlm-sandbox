from config import SANDBOX_TEMPLATE
from e2b_code_interpreter import Sandbox


def inspect_result(label: str, result):
    """Print every field of an Execution result for manual inspection."""
    print(f"\n=== {label} ===")
    print(f"type(result):        {type(result)}")
    print(f"result.logs:         {result.logs}")
    print(f"type(logs.stdout):   {type(result.logs.stdout)}")
    print(f"logs.stdout:         {repr(result.logs.stdout)}")
    print(f"type(logs.stderr):   {type(result.logs.stderr)}")
    print(f"logs.stderr:         {repr(result.logs.stderr)}")
    print(f"result.error:        {repr(result.error)}")
    if result.error:
        print(f"  error.name:        {result.error.name}")
        print(f"  error.value:       {result.error.value}")
        print(f"  type(traceback):   {type(result.error.traceback)}")
        print(f"  error.traceback:   {repr(result.error.traceback)}")
    print(f"result.results:      {repr(result.results)}")


if __name__ == "__main__":
    sandbox = Sandbox.create(template=SANDBOX_TEMPLATE, timeout=60)
    print(f"Sandbox created: {sandbox.sandbox_id}")

    inspect_result("stdout only", sandbox.run_code('print("hello world")'))
    inspect_result("multi-line stdout", sandbox.run_code('print("line1")\nprint("line2")'))
    inspect_result("stderr only", sandbox.run_code('import sys; sys.stderr.write("warning\\n")'))
    inspect_result("stdout + stderr", sandbox.run_code('print("out"); import sys; sys.stderr.write("err\\n")'))
    inspect_result("runtime error", sandbox.run_code('1 / 0'))
    inspect_result("multi-line error", sandbox.run_code('import pandas as pd\ndf1 = pd.DataFrame({"a": [1]})\ndf2 = pd.read_csv("/nonexistent.csv")\ndf3 = pd.DataFrame({"b": [2]})'))
    inspect_result("no output", sandbox.run_code('x = 42'))

    sandbox.kill()
    print("\nSandbox killed.")
