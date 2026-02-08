"""Pipeline component interfaces for dependency injection."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class Downloader(ABC):
    """Interface for downloading media."""

    @abstractmethod
    async def download(self, url: str, output_dir: Path) -> Path:
        """Download media and return path to downloaded file."""
        pass


class MediaConverter(ABC):
    """Interface for media conversion."""

    @abstractmethod
    async def convert_to_wav(self, input_path: Path, output_path: Path) -> Path:
        """Convert media to standard WAV format (16kHz, mono, PCM 16-bit)."""
        pass


class VadProcessor(ABC):
    """Interface for Voice Activity Detection processing."""

    @abstractmethod
    async def process(self, input_path: Path, output_path: Path) -> Path:
        """Process audio with VAD and return path to processed file."""
        pass


class TranscriberClient(ABC):
    """Interface for transcription client."""

    @abstractmethod
    async def transcribe(
        self,
        audio_path: Path,
        language: str
    ) -> tuple[str, list[dict]]:
        """
        Transcribe audio and return (raw_transcript, chunks).
        Chunks format: [{"i": 0, "start_sec": 0, "end_sec": 10, "text": "...", "detected_language": "no"}]
        """
        pass


class SummarizerClient(ABC):
    """Interface for summarization client."""

    @abstractmethod
    async def summarize(
        self,
        transcript: str,
        chunks: list[dict],
        language: str
    ) -> str:
        """Summarize transcript and return markdown summary."""
        pass
