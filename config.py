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
    "Using the customer feedback data and product technical specs, identify the top 3 engineering changes per product that would address the most impactful customer complaints. "
    "For each recommendation, cite the relevant feedback, point to the spec constraint causing the issue, estimate whether the fix is a firmware update, component swap, or full redesign, "
    "and flag any likely impact on unit cost or MSRP."
)
