"""
SQLAlchemy models for generation jobs and certificates.
"""

import uuid
from datetime import datetime, timezone
import enum

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class CertificateStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


def _generate_id():
    return uuid.uuid4().hex[:12]


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(12), primary_key=True, default=_generate_id)
    status = Column(String(20), default=JobStatus.PENDING.value, nullable=False)
    total_certificates = Column(Integer, default=0, nullable=False)
    completed = Column(Integer, default=0, nullable=False)
    failed = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    # optional metadata the client can attach to the job
    course_name = Column(String(255), nullable=True)
    issuer_name = Column(String(255), nullable=True)

    certificates = relationship(
        "Certificate", back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Job {self.id} | {self.status} | {self.completed}/{self.total_certificates}>"


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(12), primary_key=True, default=_generate_id)
    job_id = Column(String(12), ForeignKey("generation_jobs.id"), nullable=False)
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=True)
    status = Column(String(20), default=CertificateStatus.PENDING.value, nullable=False)
    error_message = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    job = relationship("GenerationJob", back_populates="certificates")

    def __repr__(self):
        return f"<Cert {self.id} | {self.recipient_name} | {self.status}>"
