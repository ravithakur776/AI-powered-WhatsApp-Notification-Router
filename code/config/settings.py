"""System configuration settings loaded from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Data Paths
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data" / "dataset"))
MEDIA_DIR = DATA_DIR / "media"

# AI Model Configurations
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
DEFAULT_LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")

# Performance & RAG Tuning
TOP_K_HISTORY_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "5"))
FAST_PATH_ENABLED = os.getenv("FAST_PATH_ENABLED", "true").lower() == "true"
MAX_LLM_RETRIES = int(os.getenv("MAX_LLM_RETRIES", "2"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
