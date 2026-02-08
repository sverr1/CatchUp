#!/usr/bin/env python3
"""End-to-end test for CatchUp pipeline."""
import asyncio
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from catchup.core.models import Lecture, JobStatus
from catchup.core.parsing import generate_lecture_id, generate_source_uid, generate_source_uid_short
from catchup.db.database import db
from catchup.pipeline.factory import create_pipeline


async def test_full_pipeline():
    """Test the full pipeline from start to finish."""
    print("\n" + "="*80)
    print("CatchUp v1 - End-to-End Test")
    print("="*80 + "\n")

    # Initialize database
    print("[Test] Initializing database...")
    await db.init_db()
    print("  ✅ Database initialized\n")

    # Create test lecture
    test_url = "https://ntnu.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=abc123-def456-test"
    test_title = "ELE130-1 26V on 06.02 - Test Lecture"

    print("[Test] Creating test lecture...")
    print(f"  URL: {test_url}")
    print(f"  Title: {test_title}")

    # Parse metadata (simulated)
    course_code = "ELE130-1"
    lecture_date = "2026-02-06"
    source_uid = "abc123-def456-test"
    source_uid_short = generate_source_uid_short(source_uid)
    lecture_id = generate_lecture_id(course_code, lecture_date, source_uid_short)

    print(f"  Lecture ID: {lecture_id}")
    print(f"  Source UID: {source_uid}")
    print(f"  Source UID (short): {source_uid_short}\n")

    # Create lecture object
    from datetime import datetime
    lecture = Lecture(
        lecture_id=lecture_id,
        course_code=course_code,
        lecture_date=lecture_date,
        title=test_title,
        source_url=test_url,
        source_uid=source_uid,
        created_at=datetime.utcnow()
    )

    # Save to database
    lecture, created = await db.get_or_create_lecture(lecture)
    if created:
        print("  ✅ Lecture created in database")
    else:
        print("  ⚠️  Lecture already exists in database")

    # Create job
    import uuid
    from catchup.core.models import Job

    job_id = str(uuid.uuid4())
    print(f"\n[Test] Creating job: {job_id}")

    job = Job(
        job_id=job_id,
        lecture_id=lecture.lecture_id,
        status=JobStatus.QUEUED,
        progress=0.0,
        started_at=datetime.utcnow()
    )

    await db.create_job(job)
    print("  ✅ Job created\n")

    # Create pipeline with FAKE clients for testing
    print("[Test] Creating pipeline (using FAKE clients)...")
    pipeline = create_pipeline(use_fake_clients=True)
    print(f"  Downloader: {pipeline.downloader.__class__.__name__}")
    print(f"  Converter: {pipeline.converter.__class__.__name__}")
    print(f"  VAD: {pipeline.vad_processor.__class__.__name__}")
    print(f"  Transcriber: {pipeline.transcriber.__class__.__name__}")
    print(f"  Summarizer: {pipeline.summarizer.__class__.__name__}\n")

    # Run pipeline
    print("[Test] Starting pipeline execution...")
    print("-" * 80 + "\n")

    start_time = time.time()

    try:
        # Run pipeline
        await pipeline.run(job_id, lecture, "no")

        elapsed_time = time.time() - start_time
        print("\n" + "-" * 80)
        print(f"[Test] Pipeline completed in {elapsed_time:.2f} seconds\n")

        # Check job status
        print("[Test] Verifying job status...")
        job = await db.get_job(job_id)
        print(f"  Status: {job.status}")
        print(f"  Progress: {job.progress * 100:.0f}%")
        print(f"  Error: {job.error_message or 'None'}")

        if job.status != JobStatus.DONE:
            print("  ❌ Job did not complete successfully!")
            return False
        print("  ✅ Job completed successfully\n")

        # Check artifacts
        print("[Test] Verifying artifacts...")
        artifacts = await db.get_artifacts_for_lecture(lecture_id)
        print(f"  Found {len(artifacts)} artifacts:")

        artifact_types = set()
        for artifact in artifacts:
            artifact_types.add(artifact.type.value)
            path = Path(artifact.path)
            exists = path.exists()
            size = path.stat().st_size if exists else 0
            status = "✅" if exists else "❌"
            print(f"    {status} {artifact.type.value:25s} - {artifact.path} ({size} bytes)")

        # Check expected artifacts
        expected_types = {
            "audio_original_wav",
            "audio_vad_wav",
            "raw_transcript_txt",
            "transcript_chunks_json",
            "summary_md",
            "log"
        }

        missing = expected_types - artifact_types
        if missing:
            print(f"\n  ❌ Missing artifacts: {missing}")
            return False
        print("\n  ✅ All expected artifacts created\n")

        # Check log file
        print("[Test] Checking log file...")
        log_artifacts = [a for a in artifacts if a.type.value == "log"]
        if not log_artifacts:
            print("  ❌ No log file found!")
            return False

        log_path = Path(log_artifacts[0].path)
        if not log_path.exists():
            print("  ❌ Log file doesn't exist!")
            return False

        log_content = log_path.read_text(encoding='utf-8')
        log_lines = len(log_content.splitlines())
        print(f"  Log file: {log_path}")
        print(f"  Log lines: {log_lines}")
        print("  ✅ Log file created and readable\n")

        # Check summary
        print("[Test] Checking summary...")
        summary_artifacts = [a for a in artifacts if a.type.value == "summary_md"]
        if not summary_artifacts:
            print("  ❌ No summary found!")
            return False

        summary_path = Path(summary_artifacts[0].path)
        if not summary_path.exists():
            print("  ❌ Summary file doesn't exist!")
            return False

        summary_content = summary_path.read_text(encoding='utf-8')
        summary_chars = len(summary_content)
        print(f"  Summary file: {summary_path}")
        print(f"  Summary length: {summary_chars} characters")
        print("  ✅ Summary created and readable\n")

        # Print summary preview
        print("[Test] Summary preview:")
        print("-" * 80)
        print(summary_content[:500])
        if len(summary_content) > 500:
            print(f"\n... ({len(summary_content) - 500} more characters)")
        print("-" * 80 + "\n")

        return True

    except Exception as e:
        elapsed_time = time.time() - start_time
        print("\n" + "-" * 80)
        print(f"[Test] Pipeline failed after {elapsed_time:.2f} seconds\n")
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the test."""
    success = await test_full_pipeline()

    print("\n" + "="*80)
    if success:
        print("✅ END-TO-END TEST PASSED!")
        print("="*80 + "\n")
        return 0
    else:
        print("❌ END-TO-END TEST FAILED!")
        print("="*80 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
