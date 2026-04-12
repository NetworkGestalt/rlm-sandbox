import anthropic

from config import SANDBOX_WORKDIR, LLM_API_KEY, LLM_MAX_TOKENS, LLM_MODEL, MAX_TURNS, STDOUT_LIMIT, TRACEBACK_LIMIT
from sandbox.bridge import BRIDGE_SETUP_CODE, execute_with_bridge
from agent.parsing import extract_code_blocks, extract_final_var, clean_traceback
from agent.prompts import SYSTEM_PROMPT, LLM_CALL_PROMPT, nudge


def _truncate(text: str, limit: int = STDOUT_LIMIT, mode: str = "both") -> str:
    """Trim text to *limit* chars, keeping head, tail, or both ends."""
    if len(text) <= limit:
        return text
    notice = f"... [{len(text)} chars total, truncated] ..."
    if mode == "tail":
        return notice + "\n" + text[-limit:]
    if mode == "head":
        return text[:limit] + "\n" + notice
    half = limit // 2
    head_end = text.rfind("\n", 0, half)
    tail_start = text.find("\n", len(text) - half)
    if head_end <= 0:
        head_end = half
    if tail_start < 0:
        tail_start = len(text) - half
    return f"{text[:head_end]}\n{notice}\n{text[tail_start:]}"


def _format_result(result) -> str:
    """Combine stdout and error from an Execution into one string."""
    parts = []
    if result.logs.stdout:
        parts.append(_truncate("".join(result.logs.stdout), STDOUT_LIMIT, mode="both"))
    if result.error:
        parts.append("[error]\n" + _truncate(clean_traceback(result.error.traceback), TRACEBACK_LIMIT, mode="both"))
    return "\n".join(parts) or "(no output)"


def _execute(sandbox, code: str) -> str:
    """Run setup/utility code directly (no bridge needed)."""
    return _format_result(sandbox.run_code(code))


def _llm_call(client, model, prompt: str) -> str:
    """Single-turn LLM call used to service sandbox llm_call() requests."""
    response = client.messages.create(
        model=model,
        max_tokens=LLM_MAX_TOKENS,
        system=LLM_CALL_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _execute_bridged(sandbox, code: str, client, model: str) -> str:
    """Run model-generated code with llm_call() bridge support."""
    on_request = lambda prompt: _llm_call(client, model, prompt)
    return _format_result(execute_with_bridge(sandbox, code, on_request))


def _resolve_final_var(sandbox, var_name: str) -> str:
    """Retrieve a variable's value from the sandbox REPL (untruncated)."""
    result = sandbox.run_code(f"print(repr({var_name}))")
    if result.error:
        return f"[error resolving {var_name}]\n{clean_traceback(result.error.traceback)}"
    return "".join(result.logs.stdout).strip()


def initialize_repl(sandbox, task: str) -> str:
    """Inject context, llm_call bridge, and return environment metadata."""
    sandbox.files.write("/tmp/context.txt", task.encode())
    _execute(sandbox, BRIDGE_SETUP_CODE)

    setup_code = f"""
        import os

        with open("/tmp/context.txt") as f:
            context = f.read()

        files = []
        for root, dirs, filenames in os.walk("{SANDBOX_WORKDIR}"):
            for name in filenames:
                rel = os.path.relpath(os.path.join(root, name), "{SANDBOX_WORKDIR}")
                files.append(rel)

        print(f"context_length: {{len(context)}}")
        print(f"file_count: {{len(files)}}")
        for f in sorted(files)[:50]:
            print(f"  {{f}}")
        if len(files) > 50:
            print(f"  ... and {{len(files) - 50}} more")
        """

    return _execute(sandbox, setup_code)


def _noop(event):
    pass


class Interrupted(Exception):
    pass


def run(task: str, sandbox, metadata: str, model: str = LLM_MODEL,
        on_event=_noop, cancel=None) -> str:
    """Run the agent loop; set *cancel* (threading.Event) to abort between turns."""
    client = anthropic.Anthropic(api_key=LLM_API_KEY)

    messages = [
        {"role": "user", "content": f"[Environment ready]\n{metadata}"},
    ]

    on_event({"type": "init", "metadata": metadata})

    for turn in range(MAX_TURNS):
        if cancel and cancel.is_set():
            raise Interrupted()

        response = client.messages.create(
            model=model,
            max_tokens=LLM_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            # nudge is appended but not stored — steers the model without polluting history
            messages=messages + [nudge(task, turn)],
        )
        assistant_text = response.content[0].text

        if cancel and cancel.is_set():
            raise Interrupted()

        var_name = extract_final_var(assistant_text)
        if var_name:
            content = _resolve_final_var(sandbox, var_name)
            print(f"\n--- final answer ---\n{content}")
            on_event({"type": "final", "content": content})
            return content

        code_blocks = extract_code_blocks(assistant_text)

        if code_blocks:
            code = code_blocks[0]
            messages.append({"role": "assistant", "content": assistant_text})
            print(f"\n--- repl (turn {turn + 1}) ---\n{code}")
            on_event({"type": "code", "turn": turn + 1, "code": code})

            output = _execute_bridged(sandbox, code, client, model)
            print(f"\n--- output ---\n{output}")
            on_event({"type": "output", "turn": turn + 1, "output": output})

            messages.append({
                "role": "user",
                "content": (
                    f"Code executed:\n```python\n{code}\n```\n\n"
                    f"REPL output:\n{output}"
                ),
            })
        else:
            print(f"\n--- assistant (turn {turn + 1}, no code) ---\n{assistant_text}")
            messages.append({"role": "assistant", "content": assistant_text})
            on_event({"type": "text", "turn": turn + 1, "text": assistant_text})

    return "Reached maximum number of turns."
