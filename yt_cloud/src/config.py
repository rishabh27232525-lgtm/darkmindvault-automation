from pathlib import Path
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
YOUTUBE_CREDS_B64 = os.getenv("YOUTUBE_CREDS_B64")
YOUTUBE_TOKEN_B64 = os.getenv("YOUTUBE_TOKEN_B64")
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR.parent / "output"

ACTIVE_LANGUAGES = ["en", "hi"]

LANGUAGES = {
    "en": {
        "name": "English",
        "voice": "en-US-GuyNeural",
        "flag": "🇺🇸"
    },
    "hi": {
        "name": "Hindi",
        "voice": "hi-IN-MadhurNeural",
        "flag": "🇮🇳"
    }
}

# Dummy placeholders (baad me change kar sakte)
CHANNEL_NAME = "DarkMindVault"

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
