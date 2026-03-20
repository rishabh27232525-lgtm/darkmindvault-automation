"""
voice_and_captions.py — Multi-language voiceover + SRT/VTT caption generation
Uses: edge-tts (Microsoft Edge TTS — completely free, no API key)
Supports: English, Spanish, Hindi, Portuguese, Arabic, French
"""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

import edge_tts
from yt_cloud.src import config

logger = logging.getLogger(__name__)


@dataclass
class VoiceResult:
    audio_path:    Path
    srt_path:      Path      # SRT caption file (for YouTube upload)
    vtt_path:      Path      # VTT caption file (burned into video)
    cues:          list      # [{text, start, end}] for subtitle rendering
    duration:      float     # Total audio duration in seconds


class VoiceAndCaptionGenerator:
    """
    Generates voiceover audio + captions for any language.
    Automatically picks the right voice for each language.
    """

    def generate(self, text: str, lang_code: str, output_dir: Path) -> VoiceResult:
        """Generate voiceover + captions for given text and language."""
        output_dir.mkdir(parents=True, exist_ok=True)

        lang_cfg   = config.LANGUAGES[lang_code]
        voice      = lang_cfg["voice"]
        audio_path = output_dir / f"voice_{lang_code}.mp3"
        vtt_path   = output_dir / f"captions_{lang_code}.vtt"
        srt_path   = output_dir / f"captions_{lang_code}.srt"

        logger.info(f"Generating {lang_cfg['name']} voiceover with voice: {voice}")

        # Generate audio + VTT
        asyncio.run(self._generate_async(text, voice, audio_path, vtt_path))

        # Parse VTT to cue list
        cues = self._parse_vtt(vtt_path)

        # Convert VTT → SRT for YouTube upload
        self._vtt_to_srt(vtt_path, srt_path)

        # Get duration
        duration = self._get_duration(audio_path)

        logger.info(f"Voiceover ready: {duration:.1f}s | {len(cues)} caption cues")
        return VoiceResult(
            audio_path = audio_path,
            srt_path   = srt_path,
            vtt_path   = vtt_path,
            cues       = cues,
            duration   = duration,
        )

    # ─── Async TTS Generation ─────────────────────────────────

    async def _generate_async(self, text: str, voice: str, audio_path: Path, vtt_path: Path):
        communicate = edge_tts.Communicate(
            text   = text,
            voice  = voice,
            rate   = "+5%",    # Slightly faster = more engaging
            volume = "+0%"
        )
        submaker = edge_tts.SubMaker()

        with open(audio_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.create_sub(
                        (chunk["offset"], chunk["duration"]),
                        chunk["text"]
                    )

        # Write VTT — 6 words per cue for readability
        with open(vtt_path, "w", encoding="utf-8") as f:
            f.write(submaker.generate_subs(words_in_cue=6))

    # ─── Caption Parsing ──────────────────────────────────────

    def _parse_vtt(self, vtt_path: Path) -> list:
        """Parse VTT file → list of {text, start, end}."""
        cues = []
        if not vtt_path.exists():
            return cues

        content = vtt_path.read_text(encoding="utf-8")
        blocks  = content.strip().split("\n\n")

        for block in blocks:
            lines  = block.strip().split("\n")
            ts_line = next((l for l in lines if "-->" in l), None)
            if not ts_line:
                continue
            try:
                s_str, e_str = ts_line.split("-->")
                start = self._ts_to_sec(s_str.strip())
                end   = self._ts_to_sec(e_str.strip())
                text  = " ".join(l for l in lines if "-->" not in l and l.strip())
                if text:
                    cues.append({"text": text, "start": start, "end": end})
            except Exception:
                continue
        return cues

    def _vtt_to_srt(self, vtt_path: Path, srt_path: Path):
        """Convert VTT captions to SRT format for YouTube upload."""
        cues = self._parse_vtt(vtt_path)
        lines = []
        for i, cue in enumerate(cues, 1):
            start = self._sec_to_srt_ts(cue["start"])
            end   = self._sec_to_srt_ts(cue["end"])
            lines.append(f"{i}\n{start} --> {end}\n{cue['text']}\n")
        srt_path.write_text("\n".join(lines), encoding="utf-8")

    # ─── Timestamp Utilities ──────────────────────────────────

    @staticmethod
    def _ts_to_sec(ts: str) -> float:
        """HH:MM:SS.mmm → seconds"""
        ts = ts.split(".")[0]
        parts = ts.split(":")
        if len(parts) == 3:
            return int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])
        return int(parts[0])*60 + float(parts[1])

    @staticmethod
    def _sec_to_srt_ts(sec: float) -> str:
        """seconds → HH:MM:SS,mmm (SRT format)"""
        h  = int(sec // 3600)
        m  = int((sec % 3600) // 60)
        s  = int(sec % 60)
        ms = int((sec % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @staticmethod
    def _get_duration(audio_path: Path) -> float:
        """Get audio duration via ffprobe."""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_streams", str(audio_path)],
                capture_output=True, text=True, timeout=30
            )
            data = json.loads(result.stdout)
            return float(data["streams"][0]["duration"])
        except Exception:
            return 600.0  # fallback 10 min
