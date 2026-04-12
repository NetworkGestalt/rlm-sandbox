from config import SANDBOX_WORKDIR

SYSTEM_PROMPT = f"""\
You are working inside a REPL environment to complete a task.

The REPL is initialized with:
1. A `context` variable containing your task description.
2. Project files at {SANDBOX_WORKDIR}.
3. An `llm_call(prompt)` function that queries a sub-LLM and returns its response as a string.

Write exactly ONE ```repl code block per response. You will see the output before deciding your next step.
If your code raises an error, read the traceback carefully and fix the root cause before moving on.
Never silently skip or drop data — if parsing fails, investigate and fix the underlying issue.
Variables persist across executions. Store important results in variables or files, as output is truncated.
Use `llm_call()` to analyze, summarize, or reason about data that is too large or complex to handle directly.

When done, store your result in a variable and respond with FINAL_VAR(variable_name) to return it.
Prefer storing final results as a formatted summary string rather than a raw data structure.
"""


LLM_CALL_PROMPT = "You are a helpful assistant. Answer concisely based on the provided context."


def nudge(task: str, turn: int) -> dict:
    """Transient user message appended to the API call (not stored in history)."""
    base = f'Continue using the REPL environment to answer the query: "{task}". Your next action:'
    if turn == 0:
        prefix = "You have not interacted with the REPL yet. Look through the context first.\n\n"
    else:
        prefix = "The above is your previous interaction history. "
    return {"role": "user", "content": prefix + base}
