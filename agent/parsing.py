import re

_REPL_FENCE = re.compile(r"```(?:repl|python)\s*\n(.*?)\n```", re.DOTALL)
_FINAL_VAR = re.compile(r"^\s*FINAL_VAR\((.*?)\)", re.MULTILINE | re.DOTALL)
_DASH_PREFIX = re.compile(r"^-{10,}", re.MULTILINE)
_PADDED_HEADER = re.compile(r"\s{3,}(Traceback \(most recent call last\))")


def extract_code_blocks(text: str) -> list[str]:
    return [block.strip() for block in _REPL_FENCE.findall(text)]


def clean_traceback(text: str) -> str:
    """Remove IPython's decorative formatting from a traceback."""
    text = _DASH_PREFIX.sub("", text)
    text = _PADDED_HEADER.sub(r" \1", text)
    return text.strip()


def extract_final_var(text: str) -> str | None:
    """Return the variable name if the model signals completion, else None."""
    match = _FINAL_VAR.search(text)
    return match.group(1).strip() if match else None
