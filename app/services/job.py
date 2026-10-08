"""
Job processing service for asynchronous certificate generation.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import GenerationJob, Certificate, JobStatus, CertificateStatus
from app.services.certificate import generate_certificate_pdf

logger = logging.getLogger(__name__)


def create_job(
    db: Session,
    recipients: list[dict],
    course_name: str,
    issuer_name: str,
    description: str | None = None,
) -> GenerationJob:
    """Creates a new generation job and initial certificate records in pending state."""
    job = GenerationJob(
        status=JobStatus.PENDING.value,
        total_certificates=len(recipients),
        course_name=course_name,
        issuer_name=issuer_name,
        description=description or "has successfully mastered all prescribed coursework and criteria for",
    )
    db.add(job)
    db.flush()

    for recipient in recipients:
        cert = Certificate(
            job_id=job.id,
            recipient_name=recipient["name"],
            recipient_email=recipient.get("email"),
            status=CertificateStatus.PENDING.value,
        )
        db.add(cert)

    db.commit()
    db.refresh(job)
    logger.info(f"Created job {job.id} with {len(recipients)} recipients")
    return job


def process_generation_job(job_id: str, db_session_factory):
    """Background worker pipeline to process certificates and record progress."""
    db = db_session_factory()

    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        job.status = JobStatus.RUNNING.value
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()

        for cert in certificates:
            try:
                filepath = generate_certificate_pdf(
                    recipient_name=cert.recipient_name,
                    course_name=job.course_name or "Certificate of Completion",
                    issuer_name=job.issuer_name or "Organization",
                    description=job.description or "has successfully mastered all prescribed coursework and criteria for",
                    cert_id=cert.id,
                )
                cert.status = CertificateStatus.SUCCESS.value
                cert.file_path = filepath
                job.completed += 1
                logger.info(f"Generated cert {cert.id} for {cert.recipient_name}")

            except Exception as e:
                cert.status = CertificateStatus.FAILED.value
                cert.error_message = str(e)
                job.failed += 1
                logger.warning(
                    f"Failed to generate cert for {cert.recipient_name}: {e}"
                )

            job.updated_at = datetime.now(timezone.utc)
            db.commit()

        job.status = JobStatus.DONE.value
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Job {job_id} completed: {job.completed} ok, {job.failed} failed")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED.value
                job.updated_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass

    finally:
        db.close()
