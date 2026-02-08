"""Fake implementations for testing without external dependencies."""
import asyncio
import shutil
from pathlib import Path
from typing import Optional
from .interfaces import (
    Downloader,
    MediaConverter,
    VadProcessor,
    TranscriberClient,
    SummarizerClient
)


class FakeDownloader(Downloader):
    """Fake downloader that copies a fixture file."""

    def __init__(self, fixture_path: Optional[Path] = None):
        self.fixture_path = fixture_path

    async def download(self, url: str, output_dir: Path) -> Path:
        """Simulate download by copying fixture."""
        await asyncio.sleep(0.1)  # Simulate network delay

        if self.fixture_path and self.fixture_path.exists():
            output_path = output_dir / "downloaded.wav"
            shutil.copy(self.fixture_path, output_path)
            return output_path

        # Create a dummy file if no fixture provided
        output_path = output_dir / "downloaded.wav"
        output_path.write_bytes(b"RIFF....WAVE....")  # Minimal WAV header
        return output_path


class FakeMediaConverter(MediaConverter):
    """Fake converter that just copies the file."""

    async def convert_to_wav(self, input_path: Path, output_path: Path) -> Path:
        """Simulate conversion by copying."""
        await asyncio.sleep(0.1)  # Simulate processing delay
        shutil.copy(input_path, output_path)
        return output_path


class FakeVadProcessor(VadProcessor):
    """Fake VAD processor that just copies the file."""

    async def process(self, input_path: Path, output_path: Path) -> Path:
        """Simulate VAD processing by copying."""
        await asyncio.sleep(0.1)  # Simulate processing delay
        shutil.copy(input_path, output_path)
        return output_path


class FakeTranscriberClient(TranscriberClient):
    """Fake transcriber that returns deterministic text."""

    def __init__(self, transcript_text: Optional[str] = None):
        self.transcript_text = transcript_text or self._get_default_transcript()

    def _get_default_transcript(self) -> str:
        return """Dette er en test-forelesning om programmering.
Vi skal snakke om funksjoner og variabler.
Først definerer vi en funksjon som heter hello world.
Deretter kaller vi funksjonen og printer resultatet.
Dette er slutten av forelesningen."""

    async def transcribe(
        self,
        audio_path: Path,
        language: str
    ) -> tuple[str, list[dict]]:
        """Return fake transcript with chunks."""
        await asyncio.sleep(0.2)  # Simulate API delay

        # Split transcript into chunks
        lines = self.transcript_text.strip().split('\n')
        chunk_size = max(1, len(lines) // 3)  # Split into ~3 chunks

        chunks = []
        current_time = 0
        full_transcript_parts = []

        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunk_text = ' '.join(chunk_lines)
            duration = len(chunk_text) * 0.1  # Simulate ~0.1s per character

            chunks.append({
                "i": len(chunks),
                "start_sec": current_time,
                "end_sec": current_time + duration,
                "text": chunk_text,
                "detected_language": language if language != "auto" else "no"
            })

            full_transcript_parts.append(chunk_text)
            current_time += duration

        full_transcript = '\n\n'.join(full_transcript_parts)

        return full_transcript, chunks


class FakeSummarizerClient(SummarizerClient):
    """Fake summarizer that returns deterministic markdown."""

    async def summarize(
        self,
        transcript: str,
        chunks: list[dict],
        language: str
    ) -> str:
        """Return fake summary in markdown format."""
        await asyncio.sleep(0.2)  # Simulate API delay

        # Generate a simple summary based on transcript length
        word_count = len(transcript.split())

        summary = f"""# Sammendrag av forelesning

## Hovedtemaer
- Programmering og koding
- Funksjoner og variabler
- Praktiske eksempler

## Detaljert innhold

### Introduksjon
Forelesningen dekker grunnleggende programmeringskonsepter.

### Funksjoner
Vi ser på hvordan man definerer og bruker funksjoner i kode.

### Variabler
Variabler blir brukt for å lagre data i programmer.

## Konklusjon
Dette var en innføring i grunnleggende programmering.

---
*Transkribert innhold: ca. {word_count} ord*
"""

        return summary
