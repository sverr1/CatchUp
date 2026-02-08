"""Integration tests for the full pipeline with fake clients."""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.catchup.core.models import Lecture, Job, JobStatus
from src.catchup.pipeline.runner import PipelineRunner
from src.catchup.pipeline.fake_clients import (
    FakeDownloader,
    FakeMediaConverter,
    FakeVadProcessor,
    FakeTranscriberClient,
    FakeSummarizerClient
)
from src.catchup.db.database import Database


@pytest.mark.integration
@pytest.mark.asyncio
class TestPipelineIntegration:
    """Test full pipeline with fake clients (no network)."""

    @pytest.fixture
    async def test_db(self, tmp_path):
        """Create a temporary test database."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)
        await db.init_db()
        yield db

    @pytest.fixture
    def test_data_dir(self, tmp_path):
        """Create temporary data directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return data_dir

    @pytest.fixture
    def pipeline(self):
        """Create pipeline with fake clients."""
        return PipelineRunner(
            downloader=FakeDownloader(),
            converter=FakeMediaConverter(),
            vad_processor=FakeVadProcessor(),
            transcriber=FakeTranscriberClient(),
            summarizer=FakeSummarizerClient()
        )

    async def test_full_pipeline_run(
        self,
        test_db,
        test_data_dir,
        pipeline,
        monkeypatch
    ):
        """Test that full pipeline runs without errors."""
        # Patch settings to use test directories
        from src.catchup.core import config
        monkeypatch.setattr(config.settings, 'data_dir', test_data_dir)

        # Create test lecture
        lecture = Lecture(
            lecture_id="ELE130_2026-02-08_abc123de",
            course_code="ELE130",
            lecture_date="2026-02-08",
            title="ELE130 Test Lecture",
            source_url="https://example.com/test",
            source_uid="abc123def456",
            created_at=datetime.utcnow()
        )

        # Create lecture in DB
        await test_db.create_lecture(lecture)

        # Create job
        job = Job(
            job_id="test-job-123",
            lecture_id=lecture.lecture_id,
            status=JobStatus.QUEUED,
            progress=0.0,
            started_at=datetime.utcnow()
        )
        await test_db.create_job(job)

        # Patch the global db instance
        from src.catchup.db import database
        original_db = database.db
        database.db = test_db

        try:
            # Run pipeline
            await pipeline.run(job.job_id, lecture, "no")

            # Verify job status
            updated_job = await test_db.get_job(job.job_id)
            assert updated_job.status == JobStatus.DONE
            assert updated_job.progress == 1.0

            # Verify artifacts were created
            artifacts = await test_db.get_artifacts_for_lecture(lecture.lecture_id)
            assert len(artifacts) > 0

            # Check that expected artifacts exist
            artifact_types = {a.type.value for a in artifacts}
            expected_types = {
                "audio_original_wav",
                "audio_vad_wav",
                "raw_transcript_txt",
                "transcript_chunks_json",
                "summary_md"
            }
            assert expected_types.issubset(artifact_types)

            # Verify lecture directory was created
            lecture_dir = pipeline.get_lecture_dir(lecture)
            assert lecture_dir.exists()

            # Verify files exist
            assert (lecture_dir / "source_url.txt").exists()
            assert (lecture_dir / "audio_original.wav").exists()
            assert (lecture_dir / "audio_vad.wav").exists()
            assert (lecture_dir / "transcript" / "raw_transcript.txt").exists()
            assert (lecture_dir / "transcript" / "transcript_chunks.json").exists()
            assert (lecture_dir / "summary" / "summary.md").exists()

        finally:
            # Restore original db
            database.db = original_db

    async def test_pipeline_handles_errors(
        self,
        test_db,
        test_data_dir,
        monkeypatch
    ):
        """Test that pipeline handles errors gracefully."""
        from src.catchup.core import config
        monkeypatch.setattr(config.settings, 'data_dir', test_data_dir)

        # Create a pipeline with a failing downloader
        class FailingDownloader:
            async def download(self, url, output_dir):
                raise RuntimeError("Download failed!")

        pipeline = PipelineRunner(
            downloader=FailingDownloader(),
            converter=FakeMediaConverter(),
            vad_processor=FakeVadProcessor(),
            transcriber=FakeTranscriberClient(),
            summarizer=FakeSummarizerClient()
        )

        # Create test lecture
        lecture = Lecture(
            lecture_id="ELE130_2026-02-08_xyz789ab",
            course_code="ELE130",
            lecture_date="2026-02-08",
            title="ELE130 Failing Test",
            source_url="https://example.com/fail",
            source_uid="xyz789abc123",
            created_at=datetime.utcnow()
        )

        await test_db.create_lecture(lecture)

        # Create job
        job = Job(
            job_id="failing-job-123",
            lecture_id=lecture.lecture_id,
            status=JobStatus.QUEUED,
            progress=0.0,
            started_at=datetime.utcnow()
        )
        await test_db.create_job(job)

        # Patch the global db
        from src.catchup.db import database
        original_db = database.db
        database.db = test_db

        try:
            # Run pipeline (should fail)
            with pytest.raises(RuntimeError, match="Download failed"):
                await pipeline.run(job.job_id, lecture, "no")

            # Verify job status is ERROR
            updated_job = await test_db.get_job(job.job_id)
            assert updated_job.status == JobStatus.ERROR
            assert updated_job.error_message is not None
            assert "Download failed" in updated_job.error_message

        finally:
            database.db = original_db
