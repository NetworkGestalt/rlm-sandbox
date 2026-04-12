import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SANDBOX_WORKDIR = "/home/user/project"
SANDBOX_TEMPLATE = "rlm-sandbox"

LLM_MODEL = "claude-sonnet-4-20250514"
LLM_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LLM_MAX_TOKENS = 4096

MAX_TURNS = 30
STDOUT_LIMIT = 8000
TRACEBACK_LIMIT = 5000

DEFAULT_DIRECTORY = Path(__file__).parent / "demo_dir"
DEFAULT_TASK = (
    "Audit the Q3 Business Review memo against the underlying data. "
    "Identify every claim that is verifiably correct, every claim that is incorrect or inconsistent, "
    "and every claim that cannot be verified from the available data. "
    "For each discrepancy, explain what the data actually shows and suggest why the memo might differ."
)