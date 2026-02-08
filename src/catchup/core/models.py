"""Data models for CatchUp."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    VAD = "vad"
    TRANSCRIBING = "transcribing"
    SUMMARIZING = "summarizing"
    DONE = "done"
    ERROR = "error"


class ArtifactType(str, Enum):
    """Artifact type enumeration."""
    METADATA_JSON = "metadata_json"
    AUDIO_ORIGINAL_WAV = "audio_original_wav"
    AUDIO_VAD_WAV = "audio_vad_wav"
    RAW_TRANSCRIPT_TXT = "raw_transcript_txt"
    TRANSCRIPT_CHUNKS_JSON = "transcript_chunks_json"
    SUMMARY_MD = "summary_md"
    SUMMARY_JSON = "summary_json"
    LOG = "log"


class Lecture(BaseModel):
    """Lecture model."""
    lecture_id: str
    course_code: str
    lecture_date: str
    title: str
    source_url: str
    source_uid: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Job(BaseModel):
    """Job model."""
    job_id: str
    lecture_id: str
    status: JobStatus
    progress: float = 0.0  # 0..1
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class Artifact(BaseModel):
    """Artifact model."""
    artifact_id: str
    lecture_id: str
    type: ArtifactType
    path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MetadataResponse(BaseModel):
    """Response model for metadata endpoint."""
    title: str
    duration_sec: int
    course_code: str
    lecture_date: str
    source_uid: str
    source_uid_short: str
    language_suggestion: str


class JobCreateRequest(BaseModel):
    """Request model for creating a job."""
    url: str
    language: str = "auto"  # auto|no|en


class JobCreateResponse(BaseModel):
    """Response model for job creation."""
    job_id: str
    lecture_id: str


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    lecture_id: str
    status: JobStatus
    progress: float
    error_message: Optional[str] = None
    artifacts: list[str] = Field(default_factory=list)


class LectureResponse(BaseModel):
    """Response model for lecture details."""
    lecture_id: str
    course_code: str
    lecture_date: str
    title: str
    source_url: str
    artifacts: list[Artifact]
