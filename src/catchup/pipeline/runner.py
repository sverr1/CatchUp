"""Pipeline runner for CatchUp."""
import json
import uuid
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, TextIO

from .interfaces import (
    Downloader,
    MediaConverter,
    VadProcessor,
    TranscriberClient,
    SummarizerClient
)
from ..core.models import (
    Lecture,
    Job,
    Artifact,
    JobStatus,
    ArtifactType
)
from ..core.config import settings
from ..db.database import db


class TeeLogger:
    """Write to both stdout and a file."""
    def __init__(self, file: TextIO):
        self.file = file
        self.stdout = sys.stdout

    def write(self, message: str):
        self.stdout.write(message)
        self.file.write(message)
        self.file.flush()

    def flush(self):
        self.stdout.flush()
        self.file.flush()


class PipelineRunner:
    """Orchestrates the full processing pipeline."""

    def __init__(
        self,
        downloader: Downloader,
        converter: MediaConverter,
        vad_processor: VadProcessor,
        transcriber: TranscriberClient,
        summarizer: SummarizerClient
    ):
        self.downloader = downloader
        self.converter = converter
        self.vad_processor = vad_processor
        self.transcriber = transcriber
        self.summarizer = summarizer

    def get_lecture_dir(self, lecture: Lecture) -> Path:
        """Get the directory path for a lecture."""
        from ..core.parsing import generate_source_uid_short
        source_uid_short = generate_source_uid_short(lecture.source_uid)
        return settings.data_dir / lecture.course_code / lecture.lecture_date / source_uid_short

    async def run(self, job_id: str, lecture: Lecture, language: str):
        """
        Run the full pipeline for a lecture.
        Updates job status at each step.
        """
        # Get lecture directory early for log file
        lecture_dir = self.get_lecture_dir(lecture)
        lecture_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        transcript_dir = lecture_dir / "transcript"
        summary_dir = lecture_dir / "summary"
        logs_dir = lecture_dir / "logs"
        transcript_dir.mkdir(exist_ok=True)
        summary_dir.mkdir(exist_ok=True)
        logs_dir.mkdir(exist_ok=True)

        # Open log file
        log_file_path = logs_dir / f"pipeline_{job_id}.log"
        log_file = open(log_file_path, 'w', encoding='utf-8')

        # Save original stdout
        original_stdout = sys.stdout

        try:
            # Redirect stdout to both console and file
            sys.stdout = TeeLogger(log_file)

            print(f"\n{'='*80}")
            print(f"[Pipeline] Starting job {job_id}")
            print(f"[Pipeline] Lecture: {lecture.lecture_id}")
            print(f"[Pipeline] Course: {lecture.course_code}")
            print(f"[Pipeline] Title: {lecture.title}")
            print(f"[Pipeline] Language: {language}")
            print(f"[Pipeline] Log file: {log_file_path}")
            print(f"{'='*80}\n")

            print(f"[Pipeline] Lecture directory: {lecture_dir}")

            # Save source URL
            (lecture_dir / "source_url.txt").write_text(lecture.source_url)

            # Step 1: Download
            print(f"\n[Step 1/5] DOWNLOADING")
            print(f"[Pipeline] Downloader: {self.downloader.__class__.__name__}")
            await db.update_job_status(job_id, JobStatus.DOWNLOADING, progress=0.1)
            downloaded_file = await self.downloader.download(lecture.source_url, lecture_dir)
            print(f"[Pipeline] Downloaded to: {downloaded_file}")

            # Step 2: Convert to WAV
            print(f"\n[Step 2/5] CONVERTING")
            print(f"[Pipeline] Converter: {self.converter.__class__.__name__}")
            await db.update_job_status(job_id, JobStatus.CONVERTING, progress=0.2)
            audio_original = lecture_dir / "audio_original.wav"
            await self.converter.convert_to_wav(downloaded_file, audio_original)
            print(f"[Pipeline] Converted to: {audio_original}")

            # Register artifact
            await db.create_artifact(Artifact(
                artifact_id=str(uuid.uuid4()),
                lecture_id=lecture.lecture_id,
                type=ArtifactType.AUDIO_ORIGINAL_WAV,
                path=str(audio_original)
            ))

            # Step 3: VAD processing
            print(f"\n[Step 3/5] VAD PROCESSING")
            print(f"[Pipeline] VAD Processor: {self.vad_processor.__class__.__name__}")
            await db.update_job_status(job_id, JobStatus.VAD, progress=0.3)
            audio_vad = lecture_dir / "audio_vad.wav"
            await self.vad_processor.process(audio_original, audio_vad)
            print(f"[Pipeline] VAD processed to: {audio_vad}")

            # Register artifact
            await db.create_artifact(Artifact(
                artifact_id=str(uuid.uuid4()),
                lecture_id=lecture.lecture_id,
                type=ArtifactType.AUDIO_VAD_WAV,
                path=str(audio_vad)
            ))

            # Step 4: Transcribe
            print(f"\n[Step 4/5] TRANSCRIBING")
            print(f"[Pipeline] Transcriber: {self.transcriber.__class__.__name__}")
            await db.update_job_status(job_id, JobStatus.TRANSCRIBING, progress=0.4)
            raw_transcript, chunks = await self.transcriber.transcribe(audio_vad, language)
            print(f"[Pipeline] Transcribed {len(chunks)} chunks, {len(raw_transcript)} characters")

            # Save transcript artifacts
            raw_transcript_path = transcript_dir / "raw_transcript.txt"
            raw_transcript_path.write_text(raw_transcript, encoding='utf-8')

            chunks_json_path = transcript_dir / "transcript_chunks.json"
            chunks_json_path.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding='utf-8')

            # Register artifacts
            await db.create_artifact(Artifact(
                artifact_id=str(uuid.uuid4()),
                lecture_id=lecture.lecture_id,
                type=ArtifactType.RAW_TRANSCRIPT_TXT,
                path=str(raw_transcript_path)
            ))
            await db.create_artifact(Artifact(
                artifact_id=str(uuid.uuid4()),
                lecture_id=lecture.lecture_id,
                type=ArtifactType.TRANSCRIPT_CHUNKS_JSON,
                path=str(chunks_json_path)
            ))

            # Step 5: Summarize
            print(f"\n[Step 5/5] SUMMARIZING")
            print(f"[Pipeline] Summarizer: {self.summarizer.__class__.__name__}")
            await db.update_job_status(job_id, JobStatus.SUMMARIZING, progress=0.7)
            summary_md = await self.summarizer.summarize(raw_transcript, chunks, language)
            print(f"[Pipeline] Generated summary: {len(summary_md)} characters")

            # Save summary
            summary_path = summary_dir / "summary.md"
            summary_path.write_text(summary_md, encoding='utf-8')
            print(f"[Pipeline] Saved summary to: {summary_path}")

            # Register artifact
            await db.create_artifact(Artifact(
                artifact_id=str(uuid.uuid4()),
                lecture_id=lecture.lecture_id,
                type=ArtifactType.SUMMARY_MD,
                path=str(summary_path)
            ))

            # Done!
            await db.update_job_status(job_id, JobStatus.DONE, progress=1.0)
            print(f"\n{'='*80}")
            print(f"[Pipeline] ✅ Job {job_id} completed successfully!")
            print(f"[Pipeline] View at: /render/{lecture.lecture_id}")
            print(f"[Pipeline] Log saved to: {log_file_path}")
            print(f"{'='*80}\n")

        except Exception as e:
            # Log error and update job status
            error_message = str(e)
            print(f"\n{'='*80}")
            print(f"[Pipeline] ❌ Job {job_id} failed!")
            print(f"[Pipeline] Error: {error_message}")
            print(f"[Pipeline] Log saved to: {log_file_path}")
            print(f"{'='*80}\n")
            await db.update_job_status(
                job_id,
                JobStatus.ERROR,
                error_message=error_message
            )
            raise

        finally:
            # Restore original stdout and close log file
            sys.stdout = original_stdout
            log_file.close()

            # Register log file as artifact
            await db.create_artifact(Artifact(
                artifact_id=str(uuid.uuid4()),
                lecture_id=lecture.lecture_id,
                type=ArtifactType.LOG,
                path=str(log_file_path)
            ))
