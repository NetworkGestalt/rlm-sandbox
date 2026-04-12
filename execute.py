from sandbox.manager import create_sandbox
from agent.orchestrator import initialize_repl, run
from config import DEFAULT_TASK, DEFAULT_DIRECTORY

if __name__ == "__main__":
    sandbox = create_sandbox(DEFAULT_DIRECTORY)
    try:
        metadata = initialize_repl(sandbox, DEFAULT_TASK)
        print(f"\n--- repl initialized ---\n{metadata}")
        result = run(DEFAULT_TASK, sandbox, metadata)
        print(f"\n--- result ---\n{result}")
    finally:
        sandbox.kill()
