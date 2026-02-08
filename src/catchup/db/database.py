"""Database management for CatchUp."""
import aiosqlite
from pathlib import Path
from typing import Optional
from datetime import datetime
from ..core.models import Lecture, Job, Artifact, JobStatus, ArtifactType
from ..core.config import settings


class Database:
    """Database manager for CatchUp."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.sqlite_path

    async def init_db(self):
        """Initialize database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create lectures table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS lectures (
                    lecture_id TEXT PRIMARY KEY,
                    course_code TEXT NOT NULL,
                    lecture_date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    source_uid TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # Create jobs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    lecture_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    error_message TEXT,
                    started_at TEXT,
                    finished_at TEXT,
                    FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
                )
            """)

            # Create artifacts table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    lecture_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
                )
            """)

            # Create indices
            await db.execute("CREATE INDEX IF NOT EXISTS idx_lectures_course ON lectures(course_code)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_lectures_date ON lectures(lecture_date)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_lecture ON jobs(lecture_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_lecture ON artifacts(lecture_id)")

            await db.commit()

    async def get_lecture_by_uid(self, source_uid: str) -> Optional[Lecture]:
        """Get lecture by source UID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM lectures WHERE source_uid = ?",
                (source_uid,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Lecture(**dict(row))
                return None

    async def create_lecture(self, lecture: Lecture) -> Lecture:
        """Create a new lecture."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO lectures (lecture_id, course_code, lecture_date, title, source_url, source_uid, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                lecture.lecture_id,
                lecture.course_code,
                lecture.lecture_date,
                lecture.title,
                lecture.source_url,
                lecture.source_uid,
                lecture.created_at.isoformat()
            ))
            await db.commit()
        return lecture

    async def get_or_create_lecture(self, lecture: Lecture) -> tuple[Lecture, bool]:
        """Get existing lecture or create new one. Returns (lecture, created)."""
        existing = await self.get_lecture_by_uid(lecture.source_uid)
        if existing:
            return existing, False
        created = await self.create_lecture(lecture)
        return created, True

    async def create_job(self, job: Job) -> Job:
        """Create a new job."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO jobs (job_id, lecture_id, status, progress, error_message, started_at, finished_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id,
                job.lecture_id,
                job.status.value,
                job.progress,
                job.error_message,
                job.started_at.isoformat() if job.started_at else None,
                job.finished_at.isoformat() if job.finished_at else None
            ))
            await db.commit()
        return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    data = dict(row)
                    data['status'] = JobStatus(data['status'])
                    if data['started_at']:
                        data['started_at'] = datetime.fromisoformat(data['started_at'])
                    if data['finished_at']:
                        data['finished_at'] = datetime.fromisoformat(data['finished_at'])
                    return Job(**data)
                return None

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        progress: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        """Update job status."""
        async with aiosqlite.connect(self.db_path) as db:
            updates = ["status = ?"]
            params = [status.value]

            if progress is not None:
                updates.append("progress = ?")
                params.append(progress)

            if error_message is not None:
                updates.append("error_message = ?")
                params.append(error_message)

            if status == JobStatus.DONE or status == JobStatus.ERROR:
                updates.append("finished_at = ?")
                params.append(datetime.utcnow().isoformat())

            params.append(job_id)

            await db.execute(
                f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = ?",
                params
            )
            await db.commit()

    async def create_artifact(self, artifact: Artifact) -> Artifact:
        """Create a new artifact."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO artifacts (artifact_id, lecture_id, type, path, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                artifact.artifact_id,
                artifact.lecture_id,
                artifact.type.value,
                artifact.path,
                artifact.created_at.isoformat()
            ))
            await db.commit()
        return artifact

    async def get_artifacts_for_lecture(self, lecture_id: str) -> list[Artifact]:
        """Get all artifacts for a lecture."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM artifacts WHERE lecture_id = ?",
                (lecture_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    Artifact(
                        artifact_id=row['artifact_id'],
                        lecture_id=row['lecture_id'],
                        type=ArtifactType(row['type']),
                        path=row['path'],
                        created_at=datetime.fromisoformat(row['created_at'])
                    )
                    for row in rows
                ]

    async def get_courses(self) -> list[str]:
        """Get list of all course codes."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT DISTINCT course_code FROM lectures ORDER BY course_code"
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_dates_for_course(self, course_code: str) -> list[str]:
        """Get list of dates for a course."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT DISTINCT lecture_date FROM lectures WHERE course_code = ? ORDER BY lecture_date DESC",
                (course_code,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_lectures_for_course_and_date(self, course_code: str, date: str) -> list[Lecture]:
        """Get lectures for a specific course and date."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM lectures WHERE course_code = ? AND lecture_date = ? ORDER BY created_at DESC",
                (course_code, date)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Lecture(**dict(row)) for row in rows]

    async def get_lecture(self, lecture_id: str) -> Optional[Lecture]:
        """Get lecture by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM lectures WHERE lecture_id = ?",
                (lecture_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Lecture(**dict(row))
                return None


# Global database instance
db = Database()
