"""
Pydantic schemas for request validation and response models.
"""

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class RecipientInput(BaseModel):
    name: str
    email: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Recipient name cannot be blank")
        if len(cleaned) > 200:
            raise ValueError("Recipient name exceeds 200 characters limit")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v):
        if v is None:
            return v
        v = v.strip()
        if v == "":
            return None
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v


class JobCreateRequest(BaseModel):
    recipients: list[RecipientInput]
    course_name: Optional[str] = "Certificate of Completion"
    issuer_name: Optional[str] = "Organization"

    @field_validator("recipients")
    @classmethod
    def must_have_recipients(cls, v):
        if not v:
            raise ValueError("At least one recipient is required")
        if len(v) > 500:
            raise ValueError("Maximum 500 recipients allowed per batch")
        return v


# --- Response schemas ---

class CertificateResponse(BaseModel):
    id: str
    job_id: str
    recipient_name: str
    recipient_email: Optional[str]
    status: str
    error_message: Optional[str]
    file_path: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    id: str
    status: str
    total_certificates: int
    completed: int
    failed: int
    course_name: Optional[str]
    issuer_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobDetailResponse(JobResponse):
    """same as JobResponse but includes the individual certificate details"""
    certificates: list[CertificateResponse] = []

    model_config = {"from_attributes": True}


class JobCreateResponse(BaseModel):
    """what the client gets back right after submitting a job"""
    job_id: str
    status: str
    total_certificates: int
    message: str
