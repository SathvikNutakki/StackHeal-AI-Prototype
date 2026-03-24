"""
config.py — single source of truth for env vars.
Every agent imports `GROQ_API_KEY` from here instead of hard-coding it.
"""

import os
from dotenv import load_dotenv

# Load .env that sits next to this file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    raise EnvironmentError(
        "GROQ_API_KEY is missing. "
        "Add it to backend/.env as:  GROQ_API_KEY=gsk_..."
    )
