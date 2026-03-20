"""
groq_ai.py — All AI tasks using Groq API (Free, Fastest LLM API)
Handles: Topic finding, Script writing, Translation, SEO metadata
Groq is free and runs Llama 3.3 70B — smarter than local Ollama
"""

import json
import random
import logging
import requests
from dataclasses import dataclass, field

from yt_cloud.src import config

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {config.GROQ_API_KEY}",
    "Content-Type":  "application/json"
}


def _groq(prompt: str, system: str = "", max_tokens: int = 3000, temp: float = 0.8) -> str:
    """Call Groq API. Returns raw text response."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        f"{config.GROQ_BASE_URL}/chat/completions",
        headers=HEADERS,
        json={
            "model":       config.GROQ_MODEL,
            "messages":    messages,
            "max_tokens":  max_tokens,
            "temperature": temp,
        },
        timeout=60
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _parse_json(text: str) -> dict | list:
    """Extract and parse JSON from LLM response."""
    # Try direct parse first
    try:
        return json.loads(text)
    except Exception:
        pass
    # Extract JSON block
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        s = text.find(start_char)
        e = text.rfind(end_char) + 1
        if s >= 0 and e > s:
            try:
                return json.loads(text[s:e])
            except Exception:
                pass
    raise ValueError(f"No JSON found in: {text[:200]}")


# ─────────────────────────────────────────────────────────────
# TOPIC FINDER
# ─────────────────────────────────────────────────────────────

def find_topic(used_topics: list) -> dict:
    """
    Use Groq to find the best topic for today's video.
    Returns: {title, keywords, search_terms, hook_question}
    """
    used_sample = random.sample(used_topics, min(10, len(used_topics)))
    avoid = ", ".join(f'"{t}"' for t in used_sample) if used_sample else "none"

    prompt = f"""You are selecting a YouTube video topic for a Dark History, Mystery & Psychology channel.

Already used topics (avoid these and similar): {avoid}

Pick the SINGLE most viral, psychologically disturbing or fascinating topic.
The topic must blend at least TWO of these three pillars:
  1. DARK HISTORY — real events, experiments, crimes, cover-ups
  2. MYSTERY — unsolved cases, disappearances, strange phenomena
  3. PSYCHOLOGY — manipulation, cults, criminal minds, dark human behavior

The topic should be:
- Deeply unsettling or psychologically gripping
- Based on real documented events or studies
- Something viewers will feel compelled to share
- Good for a 10-minute deep-dive video

Return ONLY this JSON:
{{
  "title": "SEO YouTube title, under 65 chars, use power words like 'Disturbing', 'Dark Truth', 'They Hid', 'Psychology of'",
  "raw_topic": "2-5 word description",
  "pillar": "which pillars this covers: history/mystery/psychology",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "search_terms": ["pexels search 1", "pexels search 2", "pexels search 3"],
  "hook_question": "One deeply disturbing opening question that makes viewers unable to look away"
}}"""

    raw = _groq(prompt, temp=0.9)
    data = _parse_json(raw)
    logger.info(f"Topic selected: {data.get('title')}")
    return data


# ─────────────────────────────────────────────────────────────
# SCRIPT GENERATOR
# ─────────────────────────────────────────────────────────────

SCRIPT_SYSTEM = """You are an elite YouTube scriptwriter for a Dark History, Mystery & Psychology channel.
Your scripts are:
- Written like a true-crime Netflix documentary narrator — dark, suspenseful, psychologically gripping
- Structured for MAXIMUM viewer retention — a shocking reveal or psychological twist every 90 seconds
- Full of real psychology terminology, historical facts, specific dates, names, case study numbers
- Tone: deeply unsettling yet intellectual — like the channel 'Wendigoon' meets 'Vsauce'
- Exactly 10 minutes when read at 140 words/minute (~1400 words total)
- Each script must include: one psychological concept, one dark historical event, one unsolved mystery angle
Always return valid JSON only."""

@dataclass
class Script:
    title:       str
    hook:        str           # First 45 sec — most critical
    sections:    list          # [{heading, content, duration_hint}]
    outro:       str           # Last 30 sec CTA
    full_text:   str           # Complete narration
    description: str           # YouTube description
    tags:        list          # YouTube tags
    hashtags:    list          # YouTube hashtags
    chapters:    list          # [{time, label}] for YouTube chapters


def generate_script(topic_data: dict) -> Script:
    """Generate complete 10-min script using Groq."""
    title = topic_data["title"]
    hook_q = topic_data.get("hook_question", "")

    prompt = f"""Write a highly engaging and viral 10-minute YouTube script for a Dark History, Mystery & Psychology channel.

Start with a powerful psychological hook in the first 5 seconds that creates fear, curiosity, or shock.

Use storytelling, suspense, and emotional triggers throughout the script.

Make the viewer feel uncomfortable, curious, and unable to stop watching.

Include at least one shocking real fact or disturbing example.

End with a strong psychological twist or question that stays in the viewer's mind.
Video title: "{title}"
Opening hook: "{hook_q}"

The script MUST weave together dark history, psychological analysis, and mystery.
Use real case studies, psychological terms (e.g. cognitive dissonance, dark triad, operant conditioning),
specific dates and names, and end sections with unresolved psychological questions.

Return ONLY this JSON:
{{
  "hook": "First 45 seconds. Open with the hook question in the most disturbing way possible. Build immediate dread. ~100 words.",
  "sections": [
    {{"heading": "The Dark Beginning", "content": "~220 words — set up the historical/psychological context with a specific real event", "chapter_time": "0:45"}},
    {{"heading": "The Psychology Behind It", "content": "~220 words — dive into the psychological mechanics, use real terms and studies", "chapter_time": "2:30"}},
    {{"heading": "What They Didn't Tell You", "content": "~220 words — the hidden or suppressed part of the story", "chapter_time": "4:15"}},
    {{"heading": "The Disturbing Pattern", "content": "~220 words — connect this to broader human psychology or historical pattern", "chapter_time": "6:00"}},
    {{"heading": "The Evidence", "content": "~220 words — documented proof, studies, witness accounts, data", "chapter_time": "7:45"}},
    {{"heading": "What This Means For You", "content": "~200 words — personal psychological relevance to the viewer. Make it feel real and close to home.", "chapter_time": "9:00"}}
  ],
  "outro": "Final 30 seconds. Land the most psychologically disturbing takeaway. Ask viewers: 'What does this say about human nature?' Tell them to comment, like, subscribe. Tease next dark topic. ~80 words.",
  "description": "SEO YouTube description 200 words. Include psychological terms and history keywords naturally. Add timestamps. End with 5 niche hashtags.",
  "tags": ["dark history","dark psychology","psychology facts","true crime","mind control","manipulation","human behavior","disturbing history","mystery","unsolved","dark facts","psychology explained"],
  "hashtags": ["#darkhistory","#darkpsychology","#psychology","#mystery","#truecrime","#disturbing","#mindfacts","#psychologyfacts"]
}}

IMPORTANT: Every section must contain at least one real documented fact, case study, or psychological study name."""

    raw  = _groq(prompt, system=SCRIPT_SYSTEM, max_tokens=4000, temp=0.8)
    data = _parse_json(raw)

    full_text = _build_full_text(data)
    chapters  = _build_chapters(data)

    return Script(
        title       = title,
        hook        = data.get("hook", ""),
        sections    = data.get("sections", []),
        outro       = data.get("outro", ""),
        full_text   = full_text,
        description = data.get("description", ""),
        tags        = data.get("tags", []),
        hashtags    = data.get("hashtags", []),
        chapters    = chapters,
    )


def _build_full_text(data: dict) -> str:
    parts = [data.get("hook", "")]
    for s in data.get("sections", []):
        parts.append(s.get("content", ""))
    parts.append(data.get("outro", ""))
    return "\n\n".join(p for p in parts if p)


def _build_chapters(data: dict) -> list:
    chapters = [{"time": "0:00", "label": "Introduction"}]
    for s in data.get("sections", []):
        chapters.append({
            "time":  s.get("chapter_time", ""),
            "label": s.get("heading", "")
        })
    return chapters


# ─────────────────────────────────────────────────────────────
# TRANSLATOR
# ─────────────────────────────────────────────────────────────

def translate_script(script: Script, target_lang_code: str) -> Script:
    """
    Translate a complete script to target language.
    Returns a new Script object with translated content.
    """
    lang     = config.LANGUAGES[target_lang_code]
    lang_name = lang["name"]

    logger.info(f"Translating to {lang_name}...")

    prompt = f"""Translate the following YouTube video script to {lang_name}.

Rules:
- Keep the dramatic, documentary narrator tone
- Adapt idioms naturally (don't translate literally)
- Keep all proper nouns, dates, and numbers in original form
- The translated script must sound native, not like a translation
- Translate the title, description, and all text fields

Input JSON:
{{
  "title": {json.dumps(script.title)},
  "hook": {json.dumps(script.hook)},
  "sections": {json.dumps(script.sections)},
  "outro": {json.dumps(script.outro)},
  "description": {json.dumps(script.description)},
  "tags": {json.dumps(script.tags[:8])}
}}

Return the EXACT same JSON structure but with all text translated to {lang_name}.
Return ONLY the JSON."""

    raw  = _groq(prompt, max_tokens=4000, temp=0.3)  # Low temp for accurate translation
    data = _parse_json(raw)

    full_text = _build_full_text(data)
    lang_hashtags = lang.get("hashtags", script.hashtags)

    return Script(
        title       = data.get("title", script.title),
        hook        = data.get("hook", ""),
        sections    = data.get("sections", []),
        outro       = data.get("outro", ""),
        full_text   = full_text,
        description = data.get("description", ""),
        tags        = data.get("tags", []),
        hashtags    = lang_hashtags,
        chapters    = script.chapters,
    )


# ─────────────────────────────────────────────────────────────
# METADATA GENERATOR
# ─────────────────────────────────────────────────────────────

def generate_metadata(script: Script, lang_code: str) -> dict:
    """
    Generate full YouTube upload metadata:
    - SEO description with timestamps
    - Tags (500 char limit)
    - Hashtags (top 3 shown in description)
    - Category, language
    """
    lang       = config.LANGUAGES[lang_code]
    hashtags   = script.hashtags[:8]
    hash_str   = " ".join(hashtags)

    # Build chapter timestamps for description
    chapter_text = "\n".join(
        f"{c['time']} {c['label']}"
        for c in script.chapters if c.get("time")
    )

    description = f"""{script.description}

━━━━━━━━━━━━━━━━━━━━━━
📌 CHAPTERS
━━━━━━━━━━━━━━━━━━━━━━
{chapter_text}

━━━━━━━━━━━━━━━━━━━━━━
🔔 Subscribe for daily history facts that will blow your mind!
━━━━━━━━━━━━━━━━━━━━━━

{hash_str}"""

    # Tags: max 500 chars total
    all_tags = script.tags + [t.replace("#","") for t in hashtags]
    tags_str = ""
    tags_out = []
    for tag in all_tags:
        if len(tags_str) + len(tag) + 1 < 490:
            tags_out.append(tag)
            tags_str += tag + ","

    return {
        "title":       script.title[:100],
        "description": description[:4900],
        "tags":        tags_out,
        "categoryId":  "27",         # Education
        "language":    lang["yt_lang"],
        "upload_time": lang["upload_time"],
        "defaultAudioLanguage": lang["yt_lang"],
    }
