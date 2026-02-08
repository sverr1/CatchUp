"""Real downloader implementation using yt-dlp."""
import subprocess
import json
from pathlib import Path
from typing import Optional
from ..pipeline.interfaces import Downloader
from ..core.config import settings


class YtdlpDownloader(Downloader):
    """Real downloader using yt-dlp."""

    def __init__(self, cookies_path: Optional[Path] = None):
        self.cookies_path = cookies_path or settings.cookies_path

    async def download(self, url: str, output_dir: Path) -> Path:
        """
        Download media from URL using yt-dlp.

        Strategy:
        1. Select lowest quality format with audio (to save bandwidth/time)
        2. Download to output_dir
        3. Return path to downloaded file
        """
        if not self.cookies_path.exists():
            raise FileNotFoundError(
                f"cookies.txt not found at {self.cookies_path}. "
                "This file is required for Panopto authentication."
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        # Output template
        output_template = str(output_dir / "downloaded.%(ext)s")

        try:
            # Run yt-dlp to download
            # -f "worstaudio/worst" = prefer audio-only, or lowest quality video
            # --cookies = use cookies.txt for authentication
            # --no-playlist = don't download playlists
            # -o = output template
            result = subprocess.run(
                [
                    "yt-dlp",
                    "-f", "worstaudio/worst",
                    "--cookies", str(self.cookies_path),
                    "--no-playlist",
                    "-o", output_template,
                    url
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=3600  # 1 hour timeout for large files
            )

            # Find the downloaded file
            downloaded_files = list(output_dir.glob("downloaded.*"))
            if not downloaded_files:
                raise RuntimeError("yt-dlp completed but no file was found")

            return downloaded_files[0]

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"yt-dlp download failed: {e.stderr}"
            ) from e
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "yt-dlp download timed out after 1 hour"
            )
