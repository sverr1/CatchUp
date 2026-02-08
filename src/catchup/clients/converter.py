"""Media converter using ffmpeg."""
import subprocess
from pathlib import Path
from ..pipeline.interfaces import MediaConverter


class FFmpegConverter(MediaConverter):
    """Convert media to standard WAV format using ffmpeg."""

    async def convert_to_wav(self, input_path: Path, output_path: Path) -> Path:
        """
        Convert media to standard WAV format.

        Output format:
        - 16kHz sample rate
        - Mono (1 channel)
        - PCM 16-bit signed integer
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Run ffmpeg
            # -i = input file
            # -ar 16000 = sample rate 16kHz
            # -ac 1 = mono (1 channel)
            # -c:a pcm_s16le = PCM 16-bit signed little-endian
            # -y = overwrite output file if exists
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i", str(input_path),
                    "-ar", "16000",
                    "-ac", "1",
                    "-c:a", "pcm_s16le",
                    "-y",
                    str(output_path)
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=3600  # 1 hour timeout
            )

            if not output_path.exists():
                raise RuntimeError("ffmpeg completed but output file was not created")

            return output_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"ffmpeg conversion failed: {e.stderr}"
            ) from e
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "ffmpeg conversion timed out after 1 hour"
            )
        except FileNotFoundError:
            raise RuntimeError(
                "ffmpeg not found. Please install ffmpeg: brew install ffmpeg"
            )
