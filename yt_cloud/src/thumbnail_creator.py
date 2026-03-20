"""
thumbnail_creator.py — Auto-generates eye-catching thumbnails for each language
Different color palette per language for brand distinction
"""

import logging
import random
import textwrap
import requests
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np

from yt_cloud.src import config

logger = logging.getLogger(__name__)

# Per-language color palettes — dark, unsettling, high contrast
LANG_PALETTES = {
    "en": {"bg": (5,  5,  5),   "accent": (220, 30,  30),  "text": "#FFFFFF"},  # Near-black + blood red
    "es": {"bg": (8,  0,  20),  "accent": (180, 0,   220),  "text": "#FFFFFF"},  # Dark purple
    "hi": {"bg": (15, 5,  0),   "accent": (255, 90,  0),   "text": "#FFFFFF"},  # Burnt orange
    "pt": {"bg": (0,  8,  8),   "accent": (0,  200, 180),  "text": "#FFFFFF"},  # Dark teal
    "ar": {"bg": (5,  10, 20),  "accent": (50, 140, 255),  "text": "#FFFFFF"},  # Cold blue
    "fr": {"bg": (5,  5,  15),  "accent": (140, 100, 255), "text": "#FFFFFF"},  # Deep violet
}

LANG_LABELS = {
    "en": "",
    "es": "ESPAÑOL",
    "hi": "हिंदी",
    "pt": "PORTUGUÊS",
    "ar": "عربي",
    "fr": "FRANÇAIS",
}

W, H = 1280, 720


class ThumbnailCreator:

    def create(self, title: str, search_term: str, lang_code: str, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"thumbnail_{lang_code}.jpg"

        palette  = LANG_PALETTES.get(lang_code, LANG_PALETTES["en"])
        bg_image = self._fetch_image(search_term)

        if bg_image:
            thumb = self._with_photo(bg_image, title, palette, lang_code)
        else:
            thumb = self._gradient_thumb(title, palette, lang_code)

        thumb.save(str(out_path), "JPEG", quality=95)
        logger.info(f"Thumbnail saved: {out_path.name}")
        return out_path

    # ─── With Photo ───────────────────────────────────────────

    def _with_photo(self, bg: Image.Image, title: str, palette: dict, lang: str) -> Image.Image:
        bg = self._crop(bg, W, H)
        bg = ImageEnhance.Brightness(bg).enhance(0.4)

        # Color tint
        tint = Image.new("RGBA", (W, H), tuple(palette["bg"]) + (90,))
        bg   = Image.alpha_composite(bg.convert("RGBA"), tint).convert("RGB")
        bg   = self._gradient_overlay(bg, palette["bg"])

        draw = ImageDraw.Draw(bg)
        self._draw_text(draw, title, palette, lang)
        self._draw_left_bar(draw, palette["accent"])
        self._draw_lang_badge(draw, lang, palette["accent"])
        return bg

    def _gradient_thumb(self, title: str, palette: dict, lang: str) -> Image.Image:
        img  = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)
        for y in range(H):
            r = int(palette["bg"][0] * (1 - y/H * 0.4))
            g = int(palette["bg"][1] * (1 - y/H * 0.4))
            b = min(255, int(palette["bg"][2] + y/H * 40))
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Noise overlay for texture
        noise = np.random.randint(0, 12, (H, W, 3), dtype=np.uint8)
        img   = Image.fromarray(np.clip(np.array(img) + noise, 0, 255).astype(np.uint8))

        draw = ImageDraw.Draw(img)
        self._draw_text(draw, title, palette, lang)
        self._draw_left_bar(draw, palette["accent"])
        self._draw_lang_badge(draw, lang, palette["accent"])
        return img

    # ─── Drawing Helpers ──────────────────────────────────────

    def _draw_text(self, draw: ImageDraw.Draw, title: str, palette: dict, lang: str):
        font_size = 88
        font = self._font(font_size)

        max_chars = 20 if lang not in ("ar", "hi") else 16

        thumb_text = random.choice([
            "THEY CONTROL YOU 😨",
            "DARK SECRET 😱",
            "YOU ARE NOT SAFE ⚠️",
            "HIDDEN TRUTH",
            "MIND CONTROL"
     ])
 
        lines = textwrap.wrap(thumb_text.upper(), width=max_chars)[:3]
        y_start = H // 2 - (len(lines) * (font_size + 14)) // 2

        for i, line in enumerate(lines):
        y = y_start + i * (font_size + 14)

        # Shadow
        for dx, dy in [(-3, -3), (3, 3), (-3, 3), (3, -3)]:
            draw.text((65 + dx, y + dy), line, font=font, fill=(0, 0, 0))

        # Main text
        draw.text((65, y), line, font=font, fill="white")
    # ─── Pexels Image ─────────────────────────────────────────

    def _fetch_image(self, query: str) -> Image.Image | None:
        try:
            r = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": config.PEXELS_API_KEY},
                params={"query": query, "per_page": 5, "orientation": "landscape"},
                timeout=10
            )
            if r.status_code == 200:
                photos = r.json().get("photos", [])
                if photos:
                    url  = random.choice(photos)["src"]["large2x"]
                    data = requests.get(url, timeout=20).content
                    return Image.open(BytesIO(data))
        except Exception as e:
            logger.warning(f"Image fetch failed: {e}")
        return None

    # ─── Utils ────────────────────────────────────────────────

    @staticmethod
    def _crop(img: Image.Image, tw: int, th: int) -> Image.Image:
        ratio = img.width / img.height
        if ratio > tw/th:
            nh, nw = th, int(th * ratio)
        else:
            nw, nh = tw, int(tw / ratio)
        img  = img.resize((nw, nh), Image.LANCZOS)
        left = (nw - tw) // 2
        top  = (nh - th) // 2
        return img.crop((left, top, left+tw, top+th))

    @staticmethod
    def _font(size: int) -> ImageFont.ImageFont:
        paths = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        ]
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
        return ImageFont.load_default()
