# Bulk Certificate Generator

A backend API for generating certificates in bulk. Built with FastAPI, SQLAlchemy, and ReportLab.

Submit a list of recipients, the system generates PDF certificates in the background, and you can track progress and download the results.

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
# clone and cd into the project
git clone <repo-url>
cd bulk-cert-generator

# create a virtual environment (I always do this, keeps things clean)
python -m venv venv

# activate it
# on Windows:
venv\Scripts\activate
# on macOS/Linux:
source venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

### Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

- **Web Dashboard**: `http://localhost:8000/` or `http://localhost:8000/ui`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Alternative ReDoc**: `http://localhost:8000/redoc`

### Testing Certificate Generation via Web UI

> **Note:** The whole frontend UI was generated using AI tools as an interactive dashboard to test and demonstrate the backend API.

Here is how to test the generation process in the browser:

1. Open `http://localhost:8000/` or `http://localhost:8000/ui` in your browser.
2. In the **Generator Studio** tab, enter the **Course or Award Title** and **Issuing Organization** (or keep the defaults).
3. Choose your input method:
   - **Quick Presets**: Click any sample button (e.g. *10 Students Batch* or *3 Dev Cohort*) to immediately populate the list.
   - **Table Builder**: Add rows manually by clicking *Add Recipient* and typing names/emails.
   - **CSV / Paste**:
     1. Click the **CSV / Paste** toggle button.
     2. Paste CSV-formatted text (e.g. `Alice Johnson, alice@example.com`, one per line) or click **Upload CSV** to upload `recipients_100.csv` (you can also click **Sample CSV** to download a template).
     3. **Important step**: Click the **"Parse into Table"** button. This parses the lines, automatically handles headers, and loads the recipients into the generation list.
4. Click **"Generate Certificates Now"**.
5. The UI will automatically switch to the **Live Tracker** tab, where you can watch the real-time progress bar, success metrics, and individual certificate statuses as the background worker threads process each recipient.
6. Once processing is complete:
   - Click **Preview** on any certificate to view the rendered PDF in the embedded modal viewer.
   - Click **PDF** to download an individual certificate.
   - Click **Download All (ZIP)** to download all generated certificates in a single ZIP file.
   - Switch to the **Job Archives** tab to inspect and reload past generation jobs.

### Run Tests

```bash
pytest -v
```

This runs the full test suite. Tests use a separate SQLite database so they don't mess with your actual data.

## API Usage

### 1. Submit a Certificate Generation Request

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": [
      {"name": "Alice Johnson", "email": "alice@example.com"},
      {"name": "Bob Smith", "email": "bob@example.com"},
      {"name": "Charlie Brown"}
    ],
    "course_name": "Introduction to Python",
    "issuer_name": "Tech Academy"
  }'
```

**Response (202 Accepted):**
```json
{
  "job_id": "a1b2c3d4e5f6",
  "status": "pending",
  "total_certificates": 3,
  "message": "Job created. 3 certificates queued for generation."
}
```

The `course_name` and `issuer_name` fields are optional — they default to "Certificate of Completion" and "Organization" respectively.

### 2. Check Job Status / Progress

```bash
curl http://localhost:8000/api/jobs/a1b2c3d4e5f6
```

**Response:**
```json
{
  "id": "a1b2c3d4e5f6",
  "status": "done",
  "total_certificates": 3,
  "completed": 3,
  "failed": 0,
  "course_name": "Introduction to Python",
  "issuer_name": "Tech Academy",
  "created_at": "2026-10-08T10:00:00",
  "updated_at": "2026-10-08T10:00:05",
  "certificates": [
    {
      "id": "cert_abc123",
      "recipient_name": "Alice Johnson",
      "status": "success",
      ...
    }
  ]
}
```

Job statuses:
- `pending` — job received, generation hasn't started
- `running` — actively generating certificates
- `done` — all certificates processed (check individual statuses for failures)
- `failed` — something went wrong at the job level

### 3. List Certificates for a Job

```bash
# all certificates
curl http://localhost:8000/api/jobs/a1b2c3d4e5f6/certificates

# only failed ones
curl http://localhost:8000/api/jobs/a1b2c3d4e5f6/certificates?status=failed
```

### 4. Download a Certificate

```bash
# single certificate
curl -O http://localhost:8000/api/certificates/cert_abc123/download

# all certificates as ZIP
curl -O http://localhost:8000/api/jobs/a1b2c3d4e5f6/download
```

### 5. List All Jobs

```bash
curl http://localhost:8000/api/jobs?limit=10&skip=0
```

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI app, all routes
│   ├── models.py            # SQLAlchemy models (Job, Certificate)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── database.py          # DB connection setup
│   └── services/
│       ├── certificate.py   # PDF generation logic
│       └── job.py           # Job management & background processing
├── tests/
│   ├── conftest.py          # Test fixtures
│   └── test_api.py          # API tests
├── generated_certs/         # where PDFs end up (gitignored)
├── requirements.txt
└── README.md
```

## Design Decisions

Here are the main choices I made and why:

### Why FastAPI?
I went with FastAPI over Flask/Django because:
- Built-in async support which is great for handling concurrent requests
- Automatic API documentation (Swagger UI at `/docs`)
- Pydantic integration for request validation — less boilerplate
- I've been using it in recent projects and find the DX really good

### Why SQLite?
SQLite made sense for this assignment because:
- Zero setup — no need to install a database server
- Ships with Python
- Easy to swap for Postgres/MySQL later by changing the connection string in `database.py`
- For the scale of this project, it's more than enough

### Background Processing with Threads
I chose to use Python threads for background certificate generation instead of Celery or similar:
- No external dependencies (Redis, RabbitMQ, etc.)
- Simple to understand and debug
- Good enough for this use case
- The tradeoff is that in-progress jobs are lost if the server restarts, which would need to be addressed for production

### Per-Certificate Error Handling
Each certificate is generated independently inside a try/except block, so one failure doesn't prevent the rest from being generated. After each certificate, we commit to the database so the client can see real-time progress by polling the status endpoint.

### PDF Generation with ReportLab
I picked ReportLab for generating the certificate PDFs because:
- Mature library, lots of documentation
- Fine-grained control over layout without needing HTML/CSS
- The certificate template is drawn entirely in code, so no external template files to manage
- Font scaling for long names is handled automatically

### Validation Strategy
Input validation happens at two levels:
1. **Pydantic schemas** — structural validation (required fields, types, email format)
2. **Business logic** — things like max 500 recipients per batch

This keeps the validation rules close to where they're defined and gives clear error messages.

## A Note on AI Tools

Parts of this project were developed with assistance from AI tools (which is allowed per the assignment guidelines):
- **Frontend UI**: The entire web dashboard interface (`index.html`, `style.css`, `app.js`) was AI-generated to provide an interactive visual way to test and demonstrate the backend API.
- **Backend Assistance**: AI tools were also used for ReportLab PDF coordinate positioning and initial boilerplate test fixtures.

All code has been reviewed, tested, and validated, and can be fully explained and modified.
