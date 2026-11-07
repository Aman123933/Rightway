import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"

# Load .env if present
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR.parent / ".env")

TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
ALLOWED_ORIGINS_RAW = os.getenv("ALLOWED_ORIGINS", "*").strip()
ALLOWED_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS_RAW.split(",") if o.strip()] or ["*"]
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-this-secret-admin-token").strip()
UNIVERSITY_NAME = os.getenv("UNIVERSITY_NAME", "Vishveshwarya Group of Institutions, Greater Noida").strip()

TERMS_FILE = DATA_DIR / "terms.json"
SOURCES_FILE = DATA_DIR / "sources.json"
LIBRARY_FILE = DATA_DIR / "library.json"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
