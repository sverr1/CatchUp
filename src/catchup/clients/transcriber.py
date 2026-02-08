"""Transcription client using Mistral's Voxtral model."""
import base64
from pathlib import Path
from typing import List, Tuple
from mistralai import Mistral

from ..pipeline.interfaces import TranscriberClient
from ..core.config import settings

# Optional torch imports (only needed when actually processing audio)
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class VoxtralTranscriber(TranscriberClient):
    """
    Transcription using Mistral's Voxtral model.

    Handles long audio by chunking (10-20 minutes) with overlap.
    """

    def __init__(
        self,
        api_key: str = None,
        chunk_minutes: int = None,
        chunk_overlap_sec: int = None
    ):
        if not TORCH_AVAILABLE:
            raise ImportError(
                "torch and torchaudio are required for VoxtralTranscriber. "
                "Install with: pip install -r requirements-ml.txt"
            )
        self.api_key = api_key or settings.mistral_api_key
        self.client = Mistral(api_key=self.api_key)
        self.chunk_minutes = chunk_minutes or settings.chunk_minutes
        self.chunk_overlap_sec = chunk_overlap_sec or settings.chunk_overlap_sec
        self.sample_rate = 16000

    async def transcribe(
        self,
        audio_path: Path,
        language: str
    ) -> Tuple[str, List[dict]]:
        """
        Transcribe audio with chunking for long files.

        Returns:
            (raw_transcript, chunks)

        Chunks format:
            [{"i": 0, "start_sec": 0, "end_sec": 600, "text": "...", "detected_language": "no"}]
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load audio to determine length
        waveform, sample_rate = torchaudio.load(str(audio_path))

        # Calculate chunk plan
        total_samples = waveform.shape[1]
        total_duration_sec = total_samples / sample_rate
        chunk_plan = self._calculate_chunk_plan(total_duration_sec)

        # Transcribe each chunk
        chunks = []
        transcript_parts = []

        for i, (start_sec, end_sec) in enumerate(chunk_plan):
            # Extract chunk
            chunk_audio = self._extract_chunk(
                audio_path,
                start_sec,
                end_sec
            )

            # Transcribe chunk
            text, detected_lang = await self._transcribe_chunk(
                chunk_audio,
                language
            )

            chunks.append({
                "i": i,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "text": text,
                "detected_language": detected_lang
            })

            transcript_parts.append(text)

        # Combine transcript
        raw_transcript = "\n\n".join(transcript_parts)

        return raw_transcript, chunks

    def _calculate_chunk_plan(
        self,
        total_duration_sec: float
    ) -> List[Tuple[float, float]]:
        """
        Calculate chunk boundaries.

        Returns list of (start_sec, end_sec) tuples with overlap.
        """
        chunk_duration_sec = self.chunk_minutes * 60
        overlap_sec = self.chunk_overlap_sec

        if total_duration_sec <= chunk_duration_sec:
            # No chunking needed
            return [(0, total_duration_sec)]

        chunks = []
        start = 0

        while start < total_duration_sec:
            end = min(start + chunk_duration_sec, total_duration_sec)
            chunks.append((start, end))

            if end >= total_duration_sec:
                break

            # Next chunk starts with overlap
            start = end - overlap_sec

        return chunks

    def _extract_chunk(
        self,
        audio_path: Path,
        start_sec: float,
        end_sec: float
    ) -> bytes:
        """
        Extract audio chunk and encode as base64.

        Mistral API expects base64-encoded audio.
        """
        # Load audio
        waveform, sample_rate = torchaudio.load(str(audio_path))

        # Extract chunk
        start_sample = int(start_sec * sample_rate)
        end_sample = int(end_sec * sample_rate)
        chunk_waveform = waveform[:, start_sample:end_sample]

        # Save to temporary bytes (WAV format)
        import io
        buffer = io.BytesIO()
        torchaudio.save(buffer, chunk_waveform, sample_rate, format='wav')
        buffer.seek(0)
        audio_bytes = buffer.read()

        return audio_bytes

    async def _transcribe_chunk(
        self,
        audio_bytes: bytes,
        language: str
    ) -> Tuple[str, str]:
        """
        Transcribe a single audio chunk using Mistral API.

        Returns (text, detected_language)
        """
        # Encode audio as base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        # Prepare language parameter
        lang_param = None if language == "auto" else language

        try:
            # Call Mistral API
            response = self.client.audio.transcriptions.create(
                model="whisper-large-v3",  # Mistral uses Whisper backend
                file={
                    "file_name": "audio.wav",
                    "content": audio_base64,
                },
                language=lang_param
            )

            text = response.text
            detected_language = language if language != "auto" else "no"

            return text, detected_language

        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}") from e
