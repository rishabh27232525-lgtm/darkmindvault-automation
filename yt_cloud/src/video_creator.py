"""
video_creator.py — Cloud-optimized video assembly for GitHub Actions
Memory: stays under 4GB peak (GitHub Actions has 7GB free)
Pipeline: Pexels footage → voiceover → burned subtitles → title card → export
"""

import logging
import random
import time
import requests
from pathlib import Path
import os
os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip, AudioFileClip, TextClip,
    CompositeVideoClip, concatenate_videoclips, ColorClip, ImageClip
)
import moviepy.video.fx.all as vfx

from yt_cloud.src import config
from voice_and_captions import VoiceResult

logger = logging.getLogger(__name__)

PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"


class VideoCreator:
    """Assembles complete YouTube video. Optimized for cloud runners."""

    def create(
        self,
        voice:       VoiceResult,
        search_terms: list,
        title:       str,
        lang_code:   str,
        output_dir:  Path,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"video_{lang_code}.mp4"

        logger.info("Downloading stock footage from Pexels...")
        clips_paths = self._fetch_footage(search_terms, voice.duration, output_dir)

        logger.info("Assembling footage...")
        base = self._assemble(clips_paths, voice.duration)

        logger.info("Adding voiceover...")
        audio   = AudioFileClip(str(voice.audio_path))
        video   = base.set_audio(audio)

        logger.info("Burning subtitles...")
        video   = self._burn_subtitles(video, voice.cues, lang_code)

        logger.info("Adding title card...")
        video   = self._add_title_card(video, title)

        logger.info(f"Exporting {lang_code} video → {out_path}")
        video.write_videofile(
            str(out_path),
            codec       = "libx264",
            audio_codec = "aac",
            fps         = config.FPS,
            preset      = "faster",   # Faster = less memory pressure
            threads     = 2,          # Conservative for cloud runner
            logger      = None,
            bitrate     = "2500k",
        )
        video.close()
        base.close()

        logger.info(f"Video exported: {out_path.stat().st_size / 1e6:.1f} MB")
        return out_path

    # ─── Footage ──────────────────────────────────────────────

    def _fetch_footage(self, terms: list, duration: float, output_dir: Path) -> list:
        footage_dir = output_dir / "footage"
        footage_dir.mkdir(exist_ok=True)
        paths = []
        needed_secs = duration + 60

        random.shuffle(terms)

        for i, term in enumerate(terms):
            if self._total_duration(paths) >= needed_secs:
                break
            videos = self._search_pexels(term)
            random.shuffle(videos)
            for j, vid in enumerate(videos[:2]):
                path = self._download_clip(vid, footage_dir, f"{i}_{j}")
                if path:
                    paths.append(path)
                    time.sleep(0.3)

        if not paths:
            logger.warning("No footage — using color background")
            paths = [self._make_fallback(duration, footage_dir)]

        return paths

    def _search_pexels(self, query: str) -> list:
        try:
            r = requests.get(
                PEXELS_VIDEO_URL,
                headers={"Authorization": config.PEXELS_API_KEY},
                params={"query": query, "per_page": 4, "orientation": "landscape"},
                timeout=15
            )
            if r.status_code == 200:
                return r.json().get("videos", [])
        except Exception as e:
            logger.warning(f"Pexels search failed '{query}': {e}")
        return []

    def _download_clip(self, vid: dict, save_dir: Path, name: str) -> Path | None:
        files = [f for f in vid.get("video_files", []) if f.get("width", 0) >= 1280]
        if not files:
            files = vid.get("video_files", [])
        if not files:
            return None
        files.sort(key=lambda f: f.get("width", 0), reverse=True)
        url  = files[0]["link"]
        path = save_dir / f"clip_{name}.mp4"
        if path.exists():
            return path
        try:
            r = requests.get(url, stream=True, timeout=60)
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return path
        except Exception as e:
            logger.warning(f"Download failed: {e}")
            return None

    def _total_duration(self, paths: list) -> float:
        total = 0.0
        for p in paths:
            try:
                c = VideoFileClip(str(p))
                total += c.duration
                c.close()
            except Exception:
                pass
        return total

    # ─── Assembly ─────────────────────────────────────────────

    def _assemble(self, paths: list, target: float):
        clips    = []
        for p in paths:
            try:
                c = VideoFileClip(str(p)).without_audio()
                c = c.resize((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
                clips.append(c)
            except Exception as e:
                logger.warning(f"Clip load failed {p}: {e}")

        if not clips:
            return ColorClip(
                (config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
                color=(10, 10, 30), duration=target
            )

        assembled = []
        current   = 0.0
        while current < target:
            for clip in clips:
                remaining = target - current
                if remaining <= 0:
                    break
                c = clip.subclip(0, min(clip.duration, remaining))
                c = c.crossfadein(0.4)
                assembled.append(c)
                current += c.duration

        return concatenate_videoclips(assembled, method="compose")

    # ─── Subtitles ────────────────────────────────────────────

    def _burn_subtitles(self, video, cues: list, lang_code: str):
        """Burn subtitles into video. Handles RTL languages (Arabic)."""
        if not cues:
            return video

        is_rtl = lang_code == "ar"
        sub_clips = []

        for cue in cues:
            try:
                txt = TextClip(
                    cue["text"],
                    fontsize     = config.SUBTITLE_SIZE,
                    font         = "Arial-Bold",
                    color        = config.SUBTITLE_COLOR,
                    stroke_color = config.SUBTITLE_STROKE,
                    stroke_width = config.SUBTITLE_STROKE_W,
                    method       = "caption",
                    size         = (config.VIDEO_WIDTH - 160, None),
                    align        = "right" if is_rtl else "center",
                )
                txt = (txt
                    .set_start(cue["start"])
                    .set_end(cue["end"])
                    .set_position(config.SUBTITLE_POSITION))
                sub_clips.append(txt)
            except Exception as e:
                logger.debug(f"Subtitle clip skipped: {e}")

        if sub_clips:
            return CompositeVideoClip([video] + sub_clips)
        return video

    # ─── Title Card ───────────────────────────────────────────

    def _add_title_card(self, video, title: str):
        """3-second animated title card at the start."""
        try:
            bg = ColorClip(
                (config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
                color=(8, 8, 20), duration=3
            )
            txt = (TextClip(
                title, fontsize=68, font="Arial-Bold", color="white",
                size=(config.VIDEO_WIDTH - 200, None),
                method="caption", align="center"
            ).set_position("center").set_duration(3)
             .fadein(0.5).fadeout(0.5))

            card = CompositeVideoClip([bg, txt])
            return concatenate_videoclips([card, video], method="compose")
        except Exception as e:
            logger.warning(f"Title card failed: {e}")
            return video

    # ─── Fallback ─────────────────────────────────────────────

    def _make_fallback(self, duration: float, save_dir: Path) -> Path:
        """Generate a simple animated gradient background video."""
        path = save_dir / "fallback.mp4"
        if path.exists():
            return path

        fps    = 8
        frames = []
        n      = min(int(duration * fps), 200)  # Cap to save memory

        for i in range(n):
            t   = i / fps
            img = Image.new("RGB", (config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
            draw = ImageDraw.Draw(img)
            for y in range(config.VIDEO_HEIGHT):
                r = int(5 + (y / config.VIDEO_HEIGHT) * 15)
                g = int(5 + (y / config.VIDEO_HEIGHT) * 8)
                b = int(30 + (y / config.VIDEO_HEIGHT) * 40 + 10 * abs(
                    (t % 4) / 4 - 0.5))
                draw.line([(0, y), (config.VIDEO_WIDTH, y)], fill=(r, g, b))
            frames.append(np.array(img))

        from moviepy.editor import ImageSequenceClip
        clip = ImageSequenceClip(frames, fps=fps).loop(duration=duration)
        clip.write_videofile(str(path), logger=None)
        clip.close()
        return path
