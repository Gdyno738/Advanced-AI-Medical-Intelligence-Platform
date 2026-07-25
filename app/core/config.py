"""
Central configuration for the Medical AI Platform.

All paths, constants, and environment variables are managed here.
Automatically loads from a .env file in the project root if present.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env from the project root (two levels up from app/core/config.py)
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env", override=False)

# ---------------------------------------------------------------------------
# Directory paths
# ---------------------------------------------------------------------------

MODEL_DIR  = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "model.pt"

REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DB_DIR  = BASE_DIR / "app" / "db"
DB_PATH = DB_DIR / "predictions.db"

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

IMG_SIZE    = 224
CLASS_NAMES = ["NORMAL", "PNEUMONIA"]

# ImageNet normalization constants
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# xAI Grok API (OpenAI-compatible)
XAI_API_KEY  = os.getenv("XAI_API_KEY", "").strip()
GROK_MODEL   = os.getenv("GROK_MODEL", "grok-3-mini")
XAI_BASE_URL = "https://api.x.ai/v1"

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_URL = f"sqlite:///{DB_PATH}"
