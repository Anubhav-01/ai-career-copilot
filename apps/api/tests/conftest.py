"""Test configuration.

Environment is pinned BEFORE any app import: SQLite database (file-based so
background-task sessions share state), mock LLM, hashing embedder, and a
disabled-in-practice rate limit.
"""
import os
import tempfile
import uuid
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="copilot-tests-"))
os.environ.update({
    "DATABASE_URL": f"sqlite:///{(_TMP / 'test.db').as_posix()}",
    "JWT_SECRET": "test-secret-not-for-production",
    "LLM_PROVIDER": "mock",
    "EMBEDDING_PROVIDER": "hashing",
    "REDIS_URL": "",
    "RATE_LIMIT_PER_MINUTE": "100000",
    "UPLOAD_DIR": str(_TMP / "uploads"),
    "ENVIRONMENT": "test",
})

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import get_engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    Base.metadata.create_all(bind=get_engine())
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register a fresh user per test and return bearer headers."""
    email = f"user-{uuid.uuid4().hex[:10]}@example.com"
    response = client.post("/api/auth/register", json={
        "email": email, "password": "S3curePassw0rd!", "full_name": "Test User",
    })
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_docx(paragraphs: list[str]) -> bytes:
    """Build a small in-memory DOCX resume for upload tests."""
    import io

    import docx

    document = docx.Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


SAMPLE_RESUME_LINES = [
    "Alex Morgan",
    "alex.morgan@example.com | (555) 123-4567 | github.com/alexmorgan",
    "Summary",
    "Backend engineer with a focus on Python APIs and applied AI.",
    "Skills",
    "Python, FastAPI, PostgreSQL, Docker, REST APIs, Redis, Git",
    "Experience",
    "Software Engineer - Acme Corp (2021 - 2024)",
    "- Built REST APIs using FastAPI serving 10k requests per day",
    "- Reduced query latency by 40% by tuning PostgreSQL indexes",
    "- Deployed services with Docker and GitHub Actions CI/CD",
    "Projects",
    "ResumeRanker - a semantic search tool",
    "- Implemented vector embeddings and semantic search with pgvector",
    "Education",
    "B.S. Computer Science, State University (2017 - 2021)",
]

SAMPLE_JOB_DESCRIPTION = """
We are hiring a Backend Engineer to join our platform team.

Responsibilities:
- Design and build REST APIs in Python
- Operate PostgreSQL databases in production
- Ship containerized services

Requirements:
- 2+ years of professional software engineering experience
- Strong Python skills and experience with FastAPI or Django
- Solid PostgreSQL knowledge and SQL fundamentals
- Experience with Docker and CI/CD pipelines
- Bachelor degree in Computer Science or equivalent practical experience

Nice to have:
- Kubernetes and Terraform experience
- Familiarity with Redis and message queues
- Exposure to machine learning workflows
"""


def upload_sample_resume(client: TestClient, headers: dict[str, str]) -> str:
    """Upload + wait for (synchronous test) processing; returns resume id."""
    content = make_docx(SAMPLE_RESUME_LINES)
    response = client.post(
        "/api/resumes/upload",
        headers=headers,
        files={"file": ("resume.docx", content,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"title": "Test Resume"},
    )
    assert response.status_code == 202, response.text
    resume_id = response.json()["id"]

    detail = client.get(f"/api/resumes/{resume_id}", headers=headers).json()
    assert detail["status"] == "completed", detail
    return resume_id


def create_sample_job(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post("/api/jobs/analyze", headers=headers, json={
        "title": "Backend Engineer",
        "company": "TechCo",
        "description": SAMPLE_JOB_DESCRIPTION,
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]
