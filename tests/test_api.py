"""
API tests for the bulk certificate generator.

Covers the main requirements:
- Creating a generation job
- Input validation (empty names, bad emails, empty list, too many recipients)
- Certificate generation (end-to-end)
- Job status/progress tracking
- Handling individual cert failures
- Retrieving/downloading generated certificates

I'm testing through the API layer since that's what the client actually uses.
The service layer gets exercised indirectly through these tests.
"""

import time
import os
from unittest.mock import patch

from app.models import GenerationJob, Certificate, JobStatus, CertificateStatus
from app.services.certificate import generate_certificate_pdf


# ──────────────────────────────────────────────
#   Health check
# ──────────────────────────────────────────────

def test_health_check(client):
    """make sure the server is alive"""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"


# ──────────────────────────────────────────────
#   Job creation
# ──────────────────────────────────────────────

def test_create_job_basic(client):
    """happy path — create a job with a couple recipients"""
    payload = {
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"},
        ],
        "course_name": "Intro to Python",
        "issuer_name": "Tech Academy",
    }

    resp = client.post("/api/jobs", json=payload)
    assert resp.status_code == 202
    data = resp.json()
    assert data["total_certificates"] == 2
    assert data["job_id"]  # should have an ID
    assert "queued" in data["message"].lower()


def test_create_job_minimal(client):
    """just a name, no email, default course/issuer"""
    payload = {
        "recipients": [{"name": "Charlie"}],
    }
    resp = client.post("/api/jobs", json=payload)
    assert resp.status_code == 202
    data = resp.json()
    assert data["total_certificates"] == 1


def test_create_job_many_recipients(client):
    """test with a decent number of recipients"""
    recipients = [{"name": f"Person {i}"} for i in range(50)]
    resp = client.post("/api/jobs", json={"recipients": recipients})
    assert resp.status_code == 202
    assert resp.json()["total_certificates"] == 50


# ──────────────────────────────────────────────
#   Input validation
# ──────────────────────────────────────────────

def test_reject_empty_recipients_list(client):
    """can't create a job with zero recipients"""
    resp = client.post("/api/jobs", json={"recipients": []})
    assert resp.status_code == 422


def test_reject_blank_name(client):
    """name can't be empty or just whitespace"""
    resp = client.post("/api/jobs", json={"recipients": [{"name": "   "}]})
    assert resp.status_code == 422


def test_reject_missing_name(client):
    """name is a required field"""
    resp = client.post("/api/jobs", json={"recipients": [{"email": "test@test.com"}]})
    assert resp.status_code == 422


def test_reject_bad_email(client):
    """basic email format validation"""
    resp = client.post("/api/jobs", json={
        "recipients": [{"name": "Test", "email": "not-an-email"}]
    })
    assert resp.status_code == 422


def test_reject_too_many_recipients(client):
    """we cap at 500 per request to stay sane"""
    recipients = [{"name": f"Person {i}"} for i in range(501)]
    resp = client.post("/api/jobs", json={"recipients": recipients})
    assert resp.status_code == 422


def test_long_name_is_ok(client):
    """long names should work fine, we just adjust the font size"""
    resp = client.post("/api/jobs", json={
        "recipients": [{"name": "A" * 100}]
    })
    assert resp.status_code == 202


# ──────────────────────────────────────────────
#   Job status and progress
# ──────────────────────────────────────────────

def test_get_job_status(client):
    """create a job and immediately check its status"""
    create_resp = client.post("/api/jobs", json={
        "recipients": [{"name": "Alice"}]
    })
    job_id = create_resp.json()["job_id"]

    resp = client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == job_id
    assert data["total_certificates"] == 1
    assert "certificates" in data


def test_get_nonexistent_job(client):
    """should 404 for a bogus job ID"""
    resp = client.get("/api/jobs/doesnotexist")
    assert resp.status_code == 404


def test_list_jobs(client):
    """list endpoint should return jobs we've created"""
    client.post("/api/jobs", json={"recipients": [{"name": "A"}]})
    client.post("/api/jobs", json={"recipients": [{"name": "B"}]})

    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) >= 2


def test_list_jobs_pagination(client):
    """pagination should limit results"""
    for i in range(5):
        client.post("/api/jobs", json={"recipients": [{"name": f"Person {i}"}]})

    resp = client.get("/api/jobs?limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# ──────────────────────────────────────────────
#   Certificate generation (end-to-end)
# ──────────────────────────────────────────────

def test_generation_completes(client):
    """
    Full flow: create a job, wait a bit for background generation,
    then check that certs were actually created.

    The sleep is a bit ugly but necessary since generation is async.
    In a real project I might use a webhook or polling, but for tests
    a short sleep is pragmatic.
    """
    resp = client.post("/api/jobs", json={
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@test.com"},
            {"name": "Bob Smith"},
        ],
        "course_name": "Testing 101",
    })
    job_id = resp.json()["job_id"]

    # give the background thread a moment
    time.sleep(3)

    status_resp = client.get(f"/api/jobs/{job_id}")
    data = status_resp.json()

    assert data["status"] == "done"
    assert data["completed"] == 2
    assert data["failed"] == 0


def test_certificates_have_correct_info(client):
    """verify the certificate records have the right data"""
    resp = client.post("/api/jobs", json={
        "recipients": [{"name": "Test Person", "email": "test@example.com"}],
        "course_name": "My Course",
        "issuer_name": "My Org",
    })
    job_id = resp.json()["job_id"]
    time.sleep(2)

    certs_resp = client.get(f"/api/jobs/{job_id}/certificates")
    certs = certs_resp.json()

    assert len(certs) == 1
    cert = certs[0]
    assert cert["recipient_name"] == "Test Person"
    assert cert["recipient_email"] == "test@example.com"
    assert cert["status"] == "success"
    assert cert["file_path"]  # should have a path


# ──────────────────────────────────────────────
#   Failure handling
# ──────────────────────────────────────────────

def test_individual_cert_failure_doesnt_block_others(client, db_session):
    """
    THIS IS A BIG ONE — if generating one cert fails, the others should
    still succeed. We mock the PDF generator to fail on the second call
    but succeed on the first and third.
    """
    call_count = 0
    original_generate = generate_certificate_pdf

    def flaky_generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("Simulated PDF generation failure")
        return original_generate(*args, **kwargs)

    with patch("app.services.job.generate_certificate_pdf", side_effect=flaky_generate):
        resp = client.post("/api/jobs", json={
            "recipients": [
                {"name": "Alice"},
                {"name": "Bob"},
                {"name": "Charlie"},
            ],
        })
        job_id = resp.json()["job_id"]
        time.sleep(3)

    status = client.get(f"/api/jobs/{job_id}").json()

    assert status["status"] == "done"
    assert status["completed"] == 2   # Alice and Charlie
    assert status["failed"] == 1      # Bob

    # check that we can see which one failed
    certs = client.get(f"/api/jobs/{job_id}/certificates").json()
    failed = [c for c in certs if c["status"] == "failed"]
    assert len(failed) == 1
    assert failed[0]["error_message"]  # should have the error details


# ──────────────────────────────────────────────
#   Certificate retrieval & download
# ──────────────────────────────────────────────

def test_download_certificate(client):
    """download a single generated cert"""
    resp = client.post("/api/jobs", json={
        "recipients": [{"name": "Download Test Person"}],
    })
    job_id = resp.json()["job_id"]
    time.sleep(2)

    # find the cert ID
    certs = client.get(f"/api/jobs/{job_id}/certificates").json()
    cert_id = certs[0]["id"]

    download_resp = client.get(f"/api/certificates/{cert_id}/download")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/pdf"


def test_download_nonexistent_cert(client):
    """trying to download a cert that doesn't exist"""
    resp = client.get("/api/certificates/nope123/download")
    assert resp.status_code == 404


def test_download_pending_cert_fails(client):
    """can't download a cert that hasn't been generated yet"""
    with patch("app.main.process_generation_job"):
        resp = client.post("/api/jobs", json={
            "recipients": [{"name": "Pending Person"}],
        })
        job_id = resp.json()["job_id"]

        certs = client.get(f"/api/jobs/{job_id}/certificates").json()
        assert len(certs) == 1
        assert certs[0]["status"] == "pending"
        cert_id = certs[0]["id"]
        download_resp = client.get(f"/api/certificates/{cert_id}/download")
        assert download_resp.status_code == 400
        assert "not available" in download_resp.json()["detail"]


def test_download_all_as_zip(client):
    """download all certs for a job as a ZIP file"""
    resp = client.post("/api/jobs", json={
        "recipients": [
            {"name": "Zip Person One"},
            {"name": "Zip Person Two"},
        ],
    })
    job_id = resp.json()["job_id"]
    time.sleep(3)

    download_resp = client.get(f"/api/jobs/{job_id}/download")
    assert download_resp.status_code == 200
    assert "application/zip" in download_resp.headers["content-type"]


def test_filter_certificates_by_status(client):
    """the status filter on the certificates endpoint"""
    resp = client.post("/api/jobs", json={
        "recipients": [{"name": "Filter Test"}],
    })
    job_id = resp.json()["job_id"]
    time.sleep(2)

    # filter for successful ones
    success_resp = client.get(f"/api/jobs/{job_id}/certificates?status=success")
    assert success_resp.status_code == 200

    # filter for failed ones (should be empty)
    failed_resp = client.get(f"/api/jobs/{job_id}/certificates?status=failed")
    assert failed_resp.status_code == 200
    assert len(failed_resp.json()) == 0


def test_invalid_status_filter(client):
    """passing a bogus status filter should error"""
    resp = client.post("/api/jobs", json={
        "recipients": [{"name": "Filter Err Test"}],
    })
    job_id = resp.json()["job_id"]

    resp = client.get(f"/api/jobs/{job_id}/certificates?status=banana")
    assert resp.status_code == 400


# ──────────────────────────────────────────────
#   Certificate PDF generation (unit test)
# ──────────────────────────────────────────────

def test_pdf_generation_directly():
    """
    Test the PDF generation function in isolation.
    Make sure it creates a file that actually exists.
    """
    path = generate_certificate_pdf(
        recipient_name="Unit Test Person",
        course_name="Unit Testing Course",
        issuer_name="Test Academy",
        cert_id="test001",
    )
    assert os.path.exists(path)
    assert path.endswith(".pdf")
    # check it's not empty
    assert os.path.getsize(path) > 0
    # cleanup
    os.remove(path)


def test_pdf_generation_special_characters():
    """names with special chars shouldn't crash the generator"""
    path = generate_certificate_pdf(
        recipient_name="José García-López",
        course_name="Café & Cooking",
        issuer_name="L'École",
        cert_id="test002",
    )
    assert os.path.exists(path)
    os.remove(path)


def test_create_job_with_custom_description(client):
    """ensure custom description is accepted and saved on the job"""
    custom_desc = "has demonstrated outstanding leadership and expertise in"
    resp = client.post("/api/jobs", json={
        "recipients": [{"name": "Dana Scully"}],
        "course_name": "Forensic Investigation",
        "issuer_name": "FBI Academy",
        "description": custom_desc,
    })
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    job_resp = client.get(f"/api/jobs/{job_id}")
    assert job_resp.status_code == 200
    data = job_resp.json()
    assert data["description"] == custom_desc


def test_pdf_generation_with_custom_description():
    """PDF generation accepts and renders custom certificate descriptions"""
    path = generate_certificate_pdf(
        recipient_name="Fox Mulder",
        course_name="X-Files Investigation",
        issuer_name="FBI Academy",
        description="has successfully mastered all paranormal case research and criteria for",
        cert_id="test003",
    )
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0
    os.remove(path)


def test_pdf_generation_multiline_description():
    """long descriptions that wrap into multiple lines should generate without error"""
    long_desc = (
        "for demonstrating exemplary dedication, extraordinary academic rigor, "
        "and highest order professional performance during all stages of training for"
    )
    path = generate_certificate_pdf(
        recipient_name="Walter Skinner",
        course_name="Bureau Operations",
        issuer_name="Department of Justice",
        description=long_desc,
        cert_id="test004",
    )
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0
    os.remove(path)
