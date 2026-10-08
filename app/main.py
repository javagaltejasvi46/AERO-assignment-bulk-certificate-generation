"""
Bulk Certificate Generator API.
Endpoints for creating generation jobs, polling status, and downloading certificates.
"""

import io
import os
import zipfile
import logging
from threading import Thread

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db, get_session_factory
from app.models import GenerationJob, Certificate, CertificateStatus
from app.schemas import (
    JobCreateRequest,
    JobCreateResponse,
    JobResponse,
    JobDetailResponse,
    CertificateResponse,
)
from app.services.job import create_job, process_generation_job

# logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator",
    description="API for bulk certificate generation, tracking, and retrieval.",
    version="1.0.0",
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ──────────────────────────────────────────────
#   Routes
# ──────────────────────────────────────────────


@app.get("/", tags=["health", "ui"])
def root(request: Request):
    """Serve the web dashboard for browsers, or health JSON for API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept and accept != "*/*":
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)

    return {
        "service": "Bulk Certificate Generator",
        "status": "running",
        "docs": "/docs",
        "ui": "/ui",
    }


@app.get("/ui", tags=["ui"])
def ui():
    """Direct route to the web dashboard."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="UI frontend template not found")


@app.get("/api/health", tags=["health"])
def api_health():
    """Health check endpoint."""
    return {
        "service": "Bulk Certificate Generator",
        "status": "running",
        "docs": "/docs",
    }



@app.post("/api/jobs", response_model=JobCreateResponse, status_code=202, tags=["jobs"])
def create_generation_job(request: JobCreateRequest, db: Session = Depends(get_db)):
    """Create a new certificate generation job and process it asynchronously."""
    recipients = [
        {"name": r.name, "email": r.email}
        for r in request.recipients
    ]

    job = create_job(
        db=db,
        recipients=recipients,
        course_name=request.course_name,
        issuer_name=request.issuer_name,
    )

    # Process generation in a background thread to prevent blocking
    thread = Thread(
        target=process_generation_job,
        args=(job.id, get_session_factory()),
        daemon=True,
    )
    thread.start()
    logger.info(f"Started generation job {job.id}")

    return JobCreateResponse(
        job_id=job.id,
        status=job.status,
        total_certificates=job.total_certificates,
        message=f"Job created. {job.total_certificates} certificates queued for generation.",
    )


@app.get("/api/jobs", response_model=list[JobResponse], tags=["jobs"])
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List all generation jobs, newest first.
    Supports basic pagination with skip/limit.
    """
    jobs = (
        db.query(GenerationJob)
        .order_by(GenerationJob.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return jobs


@app.get("/api/jobs/{job_id}", response_model=JobDetailResponse, tags=["jobs"])
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get detailed status for a specific job, including all individual
    certificate statuses. This is what you poll to track progress.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


@app.get(
    "/api/jobs/{job_id}/certificates",
    response_model=list[CertificateResponse],
    tags=["certificates"],
)
def get_job_certificates(
    job_id: str,
    status: str | None = Query(None, description="Filter by status: pending, success, or failed"),
    db: Session = Depends(get_db),
):
    """
    List certificates for a specific job. Optionally filter by status
    (handy if you just want to see the failures).
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    query = db.query(Certificate).filter(Certificate.job_id == job_id)

    if status:
        valid = {"pending", "success", "failed"}
        if status.lower() not in valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status filter. Use one of: {', '.join(valid)}",
            )
        query = query.filter(Certificate.status == status.lower())

    return query.all()


@app.get("/api/certificates/{cert_id}/download", tags=["certificates"])
def download_certificate(cert_id: str, db: Session = Depends(get_db)):
    """Download a single generated certificate PDF."""
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if cert.status != CertificateStatus.SUCCESS.value:
        raise HTTPException(
            status_code=400,
            detail=f"Certificate not available — status is '{cert.status}'"
            + (f" ({cert.error_message})" if cert.error_message else ""),
        )

    if not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate file is missing from disk")

    return FileResponse(
        cert.file_path,
        media_type="application/pdf",
        filename=os.path.basename(cert.file_path),
    )


@app.get("/api/jobs/{job_id}/download", tags=["jobs"])
def download_all_certificates(job_id: str, db: Session = Depends(get_db)):
    """Download all successfully generated certificates for a job as a streamed ZIP archive."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    certs = (
        db.query(Certificate)
        .filter(Certificate.job_id == job_id)
        .filter(Certificate.status == CertificateStatus.SUCCESS.value)
        .all()
    )

    if not certs:
        raise HTTPException(
            status_code=404,
            detail="No successfully generated certificates to download",
        )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for cert in certs:
            if cert.file_path and os.path.exists(cert.file_path):
                zf.write(cert.file_path, os.path.basename(cert.file_path))

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="certificates_job_{job_id}.zip"'
        },
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
