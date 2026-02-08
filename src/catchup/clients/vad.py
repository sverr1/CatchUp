"""Voice Activity Detection using Silero VAD."""
from pathlib import Path
from typing import List, Tuple, Optional
from ..pipeline.interfaces import VadProcessor
from ..core.config import settings

# Optional torch imports (only needed when actually processing audio)
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class SileroVadProcessor(VadProcessor):
    """
    Silero VAD processor with 'preserve natural pauses' policy.

    Policy:
    - Cut only LONG silences (> LONG_SILENCE_SEC)
    - Keep natural pauses/thinking pauses
    - When cutting long silence, replace with KEEP_SILENCE_SEC (not remove entirely)
    - Add padding around speech segments
    """

    def __init__(
        self,
        long_silence_sec: Optional[float] = None,
        keep_silence_sec: Optional[float] = None,
        padding_sec: Optional[float] = None
    ):
        if not TORCH_AVAILABLE:
            raise ImportError(
                "torch and torchaudio are required for SileroVadProcessor. "
                "Install with: pip install -r requirements-ml.txt"
            )
        self.long_silence_sec = long_silence_sec or settings.long_silence_sec
        self.keep_silence_sec = keep_silence_sec or settings.keep_silence_sec
        self.padding_sec = padding_sec or settings.padding_sec

        # Load Silero VAD model (lazy loading)
        self.model = None
        self.sample_rate = 16000

    def _load_model(self):
        """Load Silero VAD model (lazy loading)."""
        if self.model is None:
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            self.model = model
            self.get_speech_timestamps = utils[0]

    async def process(self, input_path: Path, output_path: Path) -> Path:
        """
        Process audio with VAD and preserve natural pauses.

        Algorithm:
        1. Run VAD to get speech segments
        2. Add padding to each segment
        3. Merge segments if gap is small
        4. For large gaps (> LONG_SILENCE_SEC): reduce to KEEP_SILENCE_SEC
        5. Write output WAV
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Load model
        self._load_model()

        # Load audio (will use soundfile backend if available, falls back to others)
        waveform, sample_rate = torchaudio.load(str(input_path), backend="soundfile")

        # Ensure mono and correct sample rate
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        if sample_rate != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sample_rate, self.sample_rate)
            waveform = resampler(waveform)
            sample_rate = self.sample_rate

        # Get speech timestamps from VAD
        speech_timestamps = self.get_speech_timestamps(
            waveform[0],
            self.model,
            sampling_rate=sample_rate
        )

        # Apply policy
        output_segments = self._apply_policy(speech_timestamps, waveform[0], sample_rate)

        # Concatenate segments
        output_waveform = self._concatenate_segments(output_segments, waveform[0])

        # Save output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        torchaudio.save(
            str(output_path),
            output_waveform.unsqueeze(0),
            sample_rate
        )

        return output_path

    def _apply_policy(
        self,
        speech_timestamps: List[dict],
        waveform: torch.Tensor,
        sample_rate: int
    ) -> List[Tuple[int, int]]:
        """
        Apply 'preserve natural pauses' policy.

        Returns list of (start_sample, end_sample) tuples.
        """
        if not speech_timestamps:
            # No speech detected, return entire audio
            return [(0, len(waveform))]

        # Convert config to samples
        padding_samples = int(self.padding_sec * sample_rate)
        long_silence_samples = int(self.long_silence_sec * sample_rate)
        keep_silence_samples = int(self.keep_silence_sec * sample_rate)

        segments = []
        current_start = None
        current_end = None

        for i, segment in enumerate(speech_timestamps):
            seg_start = max(0, segment['start'] - padding_samples)
            seg_end = min(len(waveform), segment['end'] + padding_samples)

            if current_start is None:
                # First segment
                current_start = seg_start
                current_end = seg_end
            else:
                # Check gap between current_end and seg_start
                gap = seg_start - current_end

                if gap < long_silence_samples:
                    # Small gap or overlap: merge segments
                    current_end = seg_end
                else:
                    # Large gap: close current segment and start new one
                    segments.append((current_start, current_end))

                    # Add kept silence (reduced gap)
                    silence_start = current_end
                    silence_end = silence_start + keep_silence_samples
                    segments.append((silence_start, silence_end))

                    # Start new segment
                    current_start = seg_start
                    current_end = seg_end

        # Add final segment
        if current_start is not None:
            segments.append((current_start, current_end))

        return segments

    def _concatenate_segments(
        self,
        segments: List[Tuple[int, int]],
        waveform: torch.Tensor
    ) -> torch.Tensor:
        """Concatenate audio segments."""
        chunks = []
        for start, end in segments:
            start = max(0, start)
            end = min(len(waveform), end)
            chunks.append(waveform[start:end])

        if not chunks:
            return waveform

        return torch.cat(chunks)
