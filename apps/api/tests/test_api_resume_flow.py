"""End-to-end resume workflow through the API (mock LLM, hashing embedder)."""
from tests.conftest import create_sample_job, upload_sample_resume


def test_upload_rejects_bad_extension(client, auth_headers):
    response = client.post(
        "/api/resumes/upload", headers=auth_headers,
        files={"file": ("malware.exe", b"MZ...", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_file"


def test_upload_rejects_fake_docx(client, auth_headers):
    response = client.post(
        "/api/resumes/upload", headers=auth_headers,
        files={"file": ("resume.docx", b"this is not a zip container", "application/msword")},
    )
    assert response.status_code == 400


def test_full_resume_pipeline(client, auth_headers):
    resume_id = upload_sample_resume(client, auth_headers)

    detail = client.get(f"/api/resumes/{resume_id}", headers=auth_headers).json()
    assert detail["status"] == "completed"
    assert detail["parsed"]["email"] == "alex.morgan@example.com"
    skill_names = {s["normalized"] for s in detail["skills"]}
    assert {"python", "fastapi", "postgresql", "docker"} <= skill_names
    assert all(s["evidence"] for s in detail["skills"])
    assert detail["sections"]

    # analysis
    analysis = client.post(f"/api/resumes/{resume_id}/analyze",
                           headers=auth_headers).json()
    assert 0 <= analysis["overall_score"] <= 100
    assert analysis["weights"]["ats"] == 0.25
    components = {c["key"] for c in analysis["scores"]["components"]}
    assert components == {"ats", "skills", "experience", "projects",
                          "keyword_coverage", "structure"}
    assert analysis["explanation"]

    # latest analysis is retrievable
    latest = client.get(f"/api/resumes/{resume_id}/analysis",
                        headers=auth_headers).json()
    assert latest["id"] == analysis["id"]


def test_bullet_improvement_requires_real_bullet(client, auth_headers):
    resume_id = upload_sample_resume(client, auth_headers)

    fake = client.post(
        f"/api/resumes/{resume_id}/improve-bullet", headers=auth_headers,
        json={"bullet": "Single-handedly invented the internet"},
    )
    assert fake.status_code == 422  # anti-hallucination: bullet must exist

    real = client.post(
        f"/api/resumes/{resume_id}/improve-bullet", headers=auth_headers,
        json={"bullet": "Built REST APIs using FastAPI serving 10k requests per day"},
    )
    assert real.status_code == 200
    body = real.json()
    assert body["improved"]
    assert body["rationale"]


def test_tailoring_flags_missing_evidence(client, auth_headers):
    resume_id = upload_sample_resume(client, auth_headers)
    job_id = create_sample_job(client, auth_headers)

    response = client.post(f"/api/resumes/{resume_id}/tailor/{job_id}",
                           headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["skills_to_emphasize"]
    # Kubernetes is preferred in the JD but absent from the resume: it must
    # never be suggested as a strength.
    assert "kubernetes" not in [s.lower() for s in body["skills_to_emphasize"]]


def test_user_isolation(client, auth_headers):
    resume_id = upload_sample_resume(client, auth_headers)

    import uuid
    other = client.post("/api/auth/register", json={
        "email": f"other-{uuid.uuid4().hex[:8]}@example.com",
        "password": "S3curePassw0rd!", "full_name": "Other User",
    }).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}

    assert client.get(f"/api/resumes/{resume_id}",
                      headers=other_headers).status_code == 404
    assert client.delete(f"/api/resumes/{resume_id}",
                         headers=other_headers).status_code == 404


def test_soft_delete(client, auth_headers):
    resume_id = upload_sample_resume(client, auth_headers)
    assert client.delete(f"/api/resumes/{resume_id}",
                         headers=auth_headers).status_code == 200
    assert client.get(f"/api/resumes/{resume_id}",
                      headers=auth_headers).status_code == 404
    listed = client.get("/api/resumes", headers=auth_headers).json()
    assert all(r["id"] != resume_id for r in listed)
