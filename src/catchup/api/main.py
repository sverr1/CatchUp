"""FastAPI application for CatchUp."""
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from ..core.models import (
    MetadataResponse,
    JobCreateRequest,
    JobCreateResponse,
    JobStatusResponse,
    LectureResponse,
    Lecture,
    Job,
    JobStatus,
    ArtifactType
)
from ..core.parsing import (
    extract_course_code,
    parse_date_from_title,
    generate_source_uid,
    generate_source_uid_short,
    generate_lecture_id,
    resolve_language
)
from ..core.config import settings
from ..core.rendering import create_lecture_html
from ..db.database import db
from ..clients.metadata import metadata_extractor
from ..pipeline.factory import create_pipeline


# Background tasks storage
background_jobs = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await db.init_db()
    yield


app = FastAPI(
    title="CatchUp API",
    description="API for processing lecture recordings",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# Create pipeline runner
# By default uses fake clients for development (set USE_FAKE_CLIENTS=false for production)
pipeline_runner = create_pipeline()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend UI."""
    static_path = Path(__file__).parent / "static" / "index.html"
    if static_path.exists():
        return static_path.read_text(encoding='utf-8')
    return {"message": "CatchUp API v1", "status": "running"}


@app.get("/status")
async def get_status():
    """Get system status and configuration."""
    return {
        "status": "running",
        "use_fake_clients": settings.use_fake_clients,
        "version": "1.0.0"
    }


@app.get("/metadata", response_model=MetadataResponse)
async def get_metadata(url: str = Query(..., description="Video URL")):
    """Extract metadata from URL without downloading."""
    try:
        return await metadata_extractor.extract_metadata(url)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/jobs", response_model=JobCreateResponse)
async def create_job(request: JobCreateRequest):
    """Create a new processing job."""
    try:
        # Get metadata
        metadata = await metadata_extractor.extract_metadata(request.url)

        # Resolve language
        language = resolve_language(request.language, metadata.course_code)

        # Create or get existing lecture
        lecture = Lecture(
            lecture_id=generate_lecture_id(
                metadata.course_code,
                metadata.lecture_date,
                metadata.source_uid_short
            ),
            course_code=metadata.course_code,
            lecture_date=metadata.lecture_date,
            title=metadata.title,
            source_url=request.url,
            source_uid=metadata.source_uid,
            created_at=datetime.utcnow()
        )

        # Get or create lecture in DB
        lecture, created = await db.get_or_create_lecture(lecture)

        # Create job
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            lecture_id=lecture.lecture_id,
            status=JobStatus.QUEUED,
            progress=0.0,
            started_at=datetime.utcnow()
        )

        await db.create_job(job)

        # Start pipeline in background
        asyncio.create_task(
            pipeline_runner.run(job_id, lecture, language)
        )

        return JobCreateResponse(
            job_id=job_id,
            lecture_id=lecture.lecture_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get job status and progress."""
    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get artifacts if job is done
    artifacts = []
    if job.status == JobStatus.DONE:
        artifact_list = await db.get_artifacts_for_lecture(job.lecture_id)
        artifacts = [a.path for a in artifact_list]

    return JobStatusResponse(
        job_id=job.job_id,
        lecture_id=job.lecture_id,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        artifacts=artifacts
    )


@app.get("/courses")
async def get_courses():
    """Get list of all courses."""
    courses = await db.get_courses()
    return {"courses": courses}


@app.get("/courses/{course_code}/dates")
async def get_course_dates(course_code: str):
    """Get list of dates for a course."""
    dates = await db.get_dates_for_course(course_code)
    return {"course_code": course_code, "dates": dates}


@app.get("/courses/{course_code}/{date}/lectures")
async def get_lectures_for_date(course_code: str, date: str):
    """Get lectures for a specific course and date."""
    lectures = await db.get_lectures_for_course_and_date(course_code, date)
    return {"course_code": course_code, "date": date, "lectures": lectures}


@app.get("/lectures/{lecture_id}", response_model=LectureResponse)
async def get_lecture(lecture_id: str):
    """Get lecture details with artifacts."""
    lecture = await db.get_lecture(lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    artifacts = await db.get_artifacts_for_lecture(lecture_id)

    return LectureResponse(
        lecture_id=lecture.lecture_id,
        course_code=lecture.course_code,
        lecture_date=lecture.lecture_date,
        title=lecture.title,
        source_url=lecture.source_url,
        artifacts=artifacts
    )


@app.get("/render/{lecture_id}", response_class=HTMLResponse)
async def render_lecture(lecture_id: str):
    """Render lecture summary as HTML with MathJax support."""
    lecture = await db.get_lecture(lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    # Find summary.md artifact
    artifacts = await db.get_artifacts_for_lecture(lecture_id)
    summary_artifact = None
    for artifact in artifacts:
        if artifact.type.value == "summary_md":
            summary_artifact = artifact
            break

    if not summary_artifact:
        raise HTTPException(status_code=404, detail="Summary not found")

    # Read summary markdown
    summary_path = Path(summary_artifact.path)
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Summary file not found")

    markdown_content = summary_path.read_text(encoding='utf-8')

    # Render markdown to HTML with LaTeX support
    html = create_lecture_html(
        title=lecture.title,
        course_code=lecture.course_code,
        lecture_date=lecture.lecture_date,
        markdown_content=markdown_content
    )

    return HTMLResponse(content=html)


@app.get("/logs/{lecture_id}", response_class=HTMLResponse)
async def view_logs(lecture_id: str):
    """View pipeline logs for a lecture."""
    lecture = await db.get_lecture(lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    # Find log artifacts
    artifacts = await db.get_artifacts_for_lecture(lecture_id)
    log_artifacts = [a for a in artifacts if a.type == ArtifactType.LOG]

    if not log_artifacts:
        raise HTTPException(status_code=404, detail="No logs found")

    # Read all log files
    logs_content = []
    for artifact in log_artifacts:
        log_path = Path(artifact.path)
        if log_path.exists():
            content = log_path.read_text(encoding='utf-8')
            logs_content.append(f"=== {log_path.name} ===\n\n{content}")

    combined_logs = "\n\n".join(logs_content)

    # Create simple HTML page with logs
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logs - {lecture.title}</title>
        <style>
            body {{
                font-family: monospace;
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 20px;
                margin: 0;
            }}
            .header {{
                background: #2d2d30;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 4px;
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                color: #4ec9b0;
            }}
            .header p {{
                margin: 0;
                color: #9cdcfe;
            }}
            pre {{
                background: #1e1e1e;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 20px;
                overflow-x: auto;
                line-height: 1.5;
            }}
            a {{
                color: #4ec9b0;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Pipeline Logs</h1>
            <p><strong>Lecture:</strong> {lecture.title}</p>
            <p><strong>Course:</strong> {lecture.course_code} | <strong>Date:</strong> {lecture.lecture_date}</p>
            <p><a href="/render/{lecture_id}">← Back to summary</a></p>
        </div>
        <pre>{combined_logs}</pre>
    </body>
    </html>
    """

    return HTMLResponse(content=html)
