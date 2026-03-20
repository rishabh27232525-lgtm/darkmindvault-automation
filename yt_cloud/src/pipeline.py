"""
pipeline.py — Master pipeline for ALL languages
Runs on GitHub Actions (7GB RAM, free)
Flow: Topic → Script (EN) → Translate × 5 → Voice + Video + Thumb per lang → Upload all
"""
import sys
import os
import logging
import colorlog
from datetime import datetime
import json
import random

from yt_cloud.src.groq_ai import _groq

from yt_cloud.src import config
from yt_cloud.src.groq_ai import find_topic, generate_script
from yt_cloud.src.voice_and_captions import VoiceAndCaptionGenerator
from yt_cloud.src.video_creator import VideoCreator
from yt_cloud.src.thumbnail_creator import ThumbnailCreator
from yt_cloud.src.uploader import YouTubeUploader


# ─── Logging ──────────────────────────────────────────────────────────────────

def setup_logging():
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        log_colors={"DEBUG":"cyan","INFO":"green","WARNING":"yellow","ERROR":"red"}
    ))
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)

logger = logging.getLogger(__name__)

def translate_script(script_en, lang_code):
    prompt = f"""
Translate the following YouTube script into {lang_code}.
Keep emotional tone, storytelling, and suspense.

SCRIPT:
{script_en.full_text}
"""
    response = _groq(prompt)
    
    class Script:
        def __init__(self, text, title):
            self.full_text = text
            self.title = title
    
    return Script(response, script_en.title)


def generate_metadata(script, lang_code):
    upload_times = {
        "en": "15:00",
        "hi": "18:30"
    }

    return {
        "title": f"{script.title} 😨 They Hid This From You | Dark Truth | {lang_code.upper()} | {random.randint(100,999)}",
        "description": (
    f"😱 {script.title}\n\n"
    "What if everything you know is a lie?\n\n"
    "This video exposes one of the darkest truths hidden from the world.\n\n"
    "⚠️ WARNING: Not for weak minds.\n\n"
    "👉 Hidden truth behind mind control\n"
    "👉 Dark psychological experiments\n"
    "👉 Real facts they don't want you to know\n\n"
    "👁️ Watch till the end to understand the truth.\n\n"
    "💬 Comment your thoughts\n"
    "🔥 Subscribe for more\n\n"
    "#darktruth #mindcontrol #psychology #mkultra #darksecrets #brainwashing #truth"
),
        "tags": [
            "dark truth",
            "mk ultra",
            "mind control",
            "psychology facts",
            "dark secrets"
        ],
        "upload_time": upload_times.get(lang_code, "now")
    }
    
# ─── Helpers ──────────────────────────────────────────────────────────────────

USED_FILE = config.BASE_DIR / "used_topics.json"

def load_used() -> list:
    if USED_FILE.exists():
        return json.loads(USED_FILE.read_text())
    return []

def save_used(used: list, topic: str):
    used.append(topic)
    USED_FILE.write_text(json.dumps(used, indent=2, ensure_ascii=False))


# ─── Main Pipeline ────────────────────────────────────────────────────────────

def run(upload: bool = True):
    start = datetime.now()
    logger.info("=" * 65)
    logger.info(f"  YOUTUBE AUTOMATION — {datetime.now():%Y-%m-%d}")
    logger.info(f"  Languages: {', '.join(config.ACTIVE_LANGUAGES)}")
    logger.info(f"  Upload: {'YES' if upload else 'DRY RUN'}")
    logger.info("=" * 65)

    # ── STEP 1: Find Today's Topic ─────────────────────────────
    logger.info("\n📍 STEP 1/5 — Finding viral topic...")
    used       = load_used()
    topic_data = find_topic(used)
    title_en   = topic_data["title"]
    logger.info(f"Topic: {title_en}")

    # Create output directory
    safe  = "".join(c for c in title_en if c.isalnum() or c in " -")[:45].strip()
    today = datetime.now().strftime("%Y%m%d")
    out_base = config.OUTPUT_DIR / f"{today}_{safe}"
    out_base.mkdir(parents=True, exist_ok=True)

    # Save topic data
    (out_base / "topic.json").write_text(json.dumps(topic_data, indent=2))

    # ── STEP 2: Generate English Script ────────────────────────
    logger.info("\n📝 STEP 2/5 — Generating English script...")
    script_en = generate_script(topic_data)
    logger.info(f"Script: {len(script_en.full_text.split())} words")

    # Save English script
    (out_base / "script_en.json").write_text(json.dumps({
        "title":       script_en.title,
        "full_text":   script_en.full_text,
        "description": script_en.description,
        "tags":        script_en.tags,
        "chapters":    script_en.chapters,
    }, indent=2, ensure_ascii=False))

    results = {}

    # ── STEP 3-5: Per-Language Processing ──────────────────────
    voice_gen = VoiceAndCaptionGenerator()
    vid_gen   = VideoCreator()
    thumb_gen = ThumbnailCreator()
    uploader  = YouTubeUploader() if upload else None

    for lang_code in config.ACTIVE_LANGUAGES:
        lang_name = config.LANGUAGES[lang_code]["name"]
        flag      = config.LANGUAGES[lang_code]["flag"]
        lang_dir  = out_base / lang_code
        lang_dir.mkdir(exist_ok=True)

        logger.info(f"\n{'='*55}")
        logger.info(f"  {flag} Processing: {lang_name.upper()}")
        logger.info(f"{'='*55}")

        try:
            # Translate (skip for English)
            if lang_code == "en":
                script = script_en
            else:
                logger.info(f"🌐 Translating to {lang_name}...")
                script = translate_script(script_en, lang_code)

            # Generate metadata
            meta = generate_metadata(script, lang_code)

            # Voiceover + captions
            logger.info(f"🎙️ Generating {lang_name} voiceover...")
            voice = voice_gen.generate(script.full_text, lang_code, lang_dir)

            # Video
            logger.info(f"🎬 Creating {lang_name} video...")
            search_terms = (
                topic_data.get("search_terms", []) + config.FOOTAGE_KEYWORDS[:3]
            )
            video_path = vid_gen.create(
                voice        = voice,
                search_terms = search_terms,
                title        = script.title,
                lang_code    = lang_code,
                output_dir   = lang_dir,
            )

            # Thumbnail
            
            thumb_path = None
                
            # Upload
            if upload:
                logger.info(f"📤 Uploading {lang_name} to YouTube...")
                vid_id = uploader.upload_language_version(
                    video_path     = video_path,
                    thumbnail_path = thumb_path,
                    srt_path       = voice.srt_path,
                    metadata       = meta,
                    lang_code      = lang_code,
                )
                url = f"https://youtube.com/watch?v={vid_id}"
                results[lang_code] = {"success": True, "url": url, "title": script.title}
                logger.info(f"✅ {flag} {lang_name}: {url}")
            else:
                results[lang_code] = {"success": True, "title": script.title, "url": "DRY_RUN"}

        except Exception as e:
            logger.error(f"❌ {lang_name} failed: {e}", exc_info=True)
            results[lang_code] = {"success": False, "error": str(e)}

    # ── Done ───────────────────────────────────────────────────
    save_used(used, title_en)
    elapsed = (datetime.now() - start).seconds // 60

    logger.info("\n" + "="*65)
    logger.info(f"  PIPELINE COMPLETE in {elapsed} minutes")
    logger.info(f"  Topic: {title_en}")
    logger.info("  Results:")
    for lc, r in results.items():
        flag = config.LANGUAGES[lc]["flag"]
        if r["success"]:
            logger.info(f"    {flag} {lc.upper()}: ✅  {r.get('url','')}")
        else:
            logger.info(f"    {flag} {lc.upper()}: ❌  {r.get('error','')}")
    logger.info("="*65)

    return results


# ─── Entry ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    setup_logging()
    upload = "--test" not in sys.argv
    if not upload:
        logger.info("DRY RUN mode — no uploads")
    results = run(upload=upload)
    failed  = [r for r in results.values() if not r["success"]]
    sys.exit(1 if failed else 0)
