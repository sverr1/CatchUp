"""Metadata extraction using yt-dlp."""
import json
import subprocess
from pathlib import Path
from typing import Optional
from ..core.config import settings
from ..core.parsing import (
    extract_course_code,
    parse_date_from_title,
    generate_source_uid,
    generate_source_uid_short,
    generate_lecture_id,
    get_default_language_for_course
)
from ..core.models import MetadataResponse


class MetadataExtractor:
    """Extracts metadata from video URLs using yt-dlp."""

    def __init__(self, cookies_path: Optional[Path] = None):
        self.cookies_path = cookies_path or settings.cookies_path

    async def extract_metadata(self, url: str) -> MetadataResponse:
        """
        Extract metadata from URL using yt-dlp.
        Raises exception if cookies.txt is missing or extraction fails.
        """
        if not self.cookies_path.exists():
            raise FileNotFoundError(
                f"cookies.txt not found at {self.cookies_path}. "
                "This file is required for Panopto authentication."
            )

        try:
            # Run yt-dlp with --dump-json to get metadata
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--dump-json",
                    "--cookies", str(self.cookies_path),
                    "--no-playlist",
                    url
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

            metadata = json.loads(result.stdout)

            # Extract fields
            title = metadata.get('title', 'Unknown')
            duration = int(metadata.get('duration', 0))
            video_id = metadata.get('id')

            # Parse course code and date from title
            course_code = extract_course_code(title)
            lecture_date = parse_date_from_title(title)

            # Generate source UID
            source_uid = generate_source_uid(url, video_id)
            source_uid_short = generate_source_uid_short(source_uid)

            # Generate lecture ID
            lecture_id = generate_lecture_id(course_code, lecture_date, source_uid_short)

            # Get language suggestion
            language_suggestion = get_default_language_for_course(course_code)

            return MetadataResponse(
                title=title,
                duration_sec=duration,
                course_code=course_code,
                lecture_date=lecture_date,
                source_uid=source_uid,
                source_uid_short=source_uid_short,
                language_suggestion=language_suggestion
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"yt-dlp failed to extract metadata: {e.stderr}"
            ) from e
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "yt-dlp metadata extraction timed out after 30 seconds"
            )
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Failed to parse yt-dlp JSON output: {e}"
            ) from e


# Global instance
metadata_extractor = MetadataExtractor()
