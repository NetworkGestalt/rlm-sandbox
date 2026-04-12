# rlm-sandbox

RLM-style agent with isolated E2B sandbox execution. The agent writes and runs Python in a sandboxed REPL, iterating until it produces a final answer. Sandbox code blocks can call `llm_call(prompt)` to query a sub-LLM mid-execution via a file-based bridge (the sandbox has no internet). A FastAPI/WebSocket UI streams each turn's code and output to the browser in real time.

## Setup

Requires Python 3.12+.

```bash
uv sync
```

Create a `.env` file with your API keys:

```
ANTHROPIC_API_KEY=sk-ant-...
E2B_API_KEY=e2b_...
```

## Usage

Start the web UI:

```bash
uv run python -m ui.server
```

This opens a browser at `http://127.0.0.1:8000`. Enter a project directory and task, then click **Run**.

Options:

```
--port PORT    Change the port (default: 8000)
--no-open      Don't auto-open the browser
```

### Headless mode

Run the agent without a browser using the defaults in `config.py`:

```bash
uv run python execute.py
```
