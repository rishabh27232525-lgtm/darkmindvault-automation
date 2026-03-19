"""
uploader.py — YouTube upload with captions, thumbnails, scheduled times
Uploads each language version at its optimal peak traffic time
"""

import base64
import json
import logging
import os
import pickle
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import config

logger = logging.getLogger(__name__)
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


class YouTubeUploader:
    """Handles upload, captions, thumbnails, and scheduling for all languages."""

    def __init__(self):
        self.youtube = self._auth_from_env()

    def upload_language_version(
        self,
        video_path:    Path,
        thumbnail_path: Path,
        srt_path:      Path,
        metadata:      dict,
        lang_code:     str,
    ) -> str:
        """
        Upload one language version.
        Returns YouTube video ID.
        """
        lang = config.LANGUAGES[lang_code]
        logger.info(f"Uploading {lang['name']} version: {metadata['title']}")

        # Calculate scheduled publish time
        schedule_dt = self._calc_schedule(lang["upload_time"])

        # Upload video
        video_id = self._upload_video(video_path, metadata, schedule_dt)
        logger.info(f"Video ID: {video_id}")

        # Upload thumbnail
        if thumbnail_path.exists():
            self._set_thumbnail(video_id, thumbnail_path)

        # Upload captions (SRT)
        if srt_path.exists():
            self._upload_captions(video_id, srt_path, lang_code, lang["name"])

        url = f"https://youtube.com/watch?v={video_id}"
        logger.info(f"{lang['flag']} {lang['name']} uploaded → {url} (publishes at {lang['upload_time']})")
        return video_id

    # ─── Video Upload ─────────────────────────────────────────

    def _upload_video(self, path: Path, meta: dict, schedule_dt: datetime) -> str:
        body = {
            "snippet": {
                "title":                meta["title"],
                "description":          meta["description"],
                "tags":                 meta.get("tags", []),
                "categoryId":           meta.get("categoryId", "27"),
                "defaultLanguage":      meta.get("language", "en"),
                "defaultAudioLanguage": meta.get("defaultAudioLanguage", "en"),
            },
            "status": {
                "privacyStatus":           "private",
                "publishAt":               schedule_dt.isoformat(),
                "selfDeclaredMadeForKids": False,
            }
        }

        media   = MediaFileUpload(str(path), mimetype="video/mp4", resumable=True, chunksize=50*1024*1024)
        request = self.youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Upload: {int(status.progress()*100)}%")

        return response["id"]

    # ─── Captions Upload ──────────────────────────────────────

    def _upload_captions(self, video_id: str, srt_path: Path, lang_code: str, lang_name: str):
        """Upload SRT captions to YouTube."""
        try:
            self.youtube.captions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId":      video_id,
                        "language":     lang_code,
                        "name":         f"{lang_name} (Auto-Generated)",
                        "isDraft":      False,
                    }
                },
                media_body=MediaFileUpload(str(srt_path), mimetype="text/plain")
            ).execute()
            logger.info(f"Captions uploaded: {lang_name}")
        except HttpError as e:
            logger.warning(f"Caption upload failed: {e}")

    # ─── Thumbnail ────────────────────────────────────────────

    def _set_thumbnail(self, video_id: str, thumb_path: Path):
        try:
            self.youtube.thumbnails().set(
                videoId    = video_id,
                media_body = MediaFileUpload(str(thumb_path), mimetype="image/jpeg")
            ).execute()
        except HttpError as e:
            logger.warning(f"Thumbnail failed: {e}")

    # ─── Schedule Calculation ─────────────────────────────────

    @staticmethod
    def _calc_schedule(time_str: str) -> datetime:
        """
        Convert "15:00" into today's UTC datetime.
        YouTube requires ISO 8601 UTC for scheduled publish.
        Note: Upload times in config.py are approximate — 
        YouTube scheduling is always in UTC internally.
        """
        h, m  = map(int, time_str.split(":"))
        now   = datetime.now(timezone.utc)
        sched = now.replace(hour=h, minute=m, second=0, microsecond=0)
        # If time already passed today, schedule for tomorrow
        if sched <= now:
            sched += timedelta(days=1)
        return sched

    # ─── Authentication from GitHub Secrets ───────────────────

    def _auth_from_env(self):
        """
        Load OAuth credentials from base64-encoded environment variables.
        Set as GitHub Secrets: YOUTUBE_CREDS_B64 and YOUTUBE_TOKEN_B64
        """
        # Write client_secrets.json from env var
        creds_b64 = config.YOUTUBE_CREDS_B64
        token_b64 = config.YOUTUBE_TOKEN_B64

        if not creds_b64:
            raise ValueError(
                "YOUTUBE_CREDS_B64 secret not set. "
                "See SETUP.md Step 5 to encode your client_secrets.json"
            )

        # Decode and write to temp file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="wb") as f:
            f.write(base64.b64decode(creds_b64))
            secrets_path = f.name

        creds = None
        if token_b64:
            token_bytes = base64.b64decode(token_b64)
            creds = pickle.loads(token_bytes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise ValueError(
                    "YOUTUBE_TOKEN_B64 is missing or invalid. "
                    "Run: python src/auth_setup.py on your laptop first."
                )

        os.unlink(secrets_path)
        return build("youtube", "v3", credentials=creds)
