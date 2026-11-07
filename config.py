"""
Sentinel SRE - Central configuration.

Loads environment variables from .env (python-dotenv) and validates
required credentials at import time.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- NVIDIA Nemotron (NIM, OpenAI-compatible) ---
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")

# --- Hindsight persistent memory (Vectorize) ---
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "")
HINDSIGHT_API_URL = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io")
HINDSIGHT_BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "")

# --- Startup validation ---
_REQUIRED = {
    "NVIDIA_API_KEY": NVIDIA_API_KEY,
    "HINDSIGHT_API_KEY": HINDSIGHT_API_KEY,
    "HINDSIGHT_BANK_ID": HINDSIGHT_BANK_ID,
}
_MISSING = [name for name, value in _REQUIRED.items() if not value]
if _MISSING:
    raise ValueError(
        f"Missing required environment variables in .env: {', '.join(_MISSING)}. "
        "Copy .env.example to .env and fill in your credentials."
    )