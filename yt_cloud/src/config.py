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
    "flag": "🇺🇸",
    "upload_time": "15:00"
},
"hi": {
    "name": "Hindi",
    "voice": "hi-IN-MadhurNeural",
    "flag": "🇮🇳",
    "upload_time": "19:40"
}
}

# Dummy placeholders (baad me change kar sakte)
CHANNEL_NAME = "DarkMindVault"

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

FOOTAGE_KEYWORDS = [
    "mind control experiment documentary",
    "dark psychology lab experiment",
    "human brain experiment cinematic",
    "mysterious science lab dark",
    "secret government experiment",
    "creepy medical research lab",
    "dark cinematic documentary footage",
    "psychological experiment reenactment"
]

VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
FPS = 24
