"""Seed a demo account with sample data via the public API.

Prerequisites: the API must be running (locally or via docker compose).

    python scripts/seed_demo.py --api http://localhost:8000

Creates demo@example.com / DemoPassword123! with:
  - the sample resume (uploaded + parsed + analyzed)
  - two analyzed job descriptions
  - a match + skill-gap analysis against the backend job
  - one tracked application
"""
import argparse
import io
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "samples"

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "DemoPassword123!"  # demo-only credential, documented in README


def build_docx() -> bytes:
    import docx

    lines = (SAMPLES / "sample_resume.md").read_text(encoding="utf-8").splitlines()
    document = docx.Document()
    for line in lines:
        if not line.startswith("# "):
            document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()

    client = httpx.Client(base_url=args.api, timeout=60)

    # register or login
    response = client.post("/api/auth/register", json={
        "email": DEMO_EMAIL, "password": DEMO_PASSWORD, "full_name": "Demo User",
    })
    if response.status_code == 409:
        response = client.post("/api/auth/login", json={
            "email": DEMO_EMAIL, "password": DEMO_PASSWORD,
        })
    response.raise_for_status()
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    print(f"[1/6] Demo user ready: {DEMO_EMAIL}")

    client.put("/api/profile", headers=headers, json={
        "headline": "Backend engineer exploring applied AI",
        "location": "Remote",
        "experience_years": 3,
        "target_roles": ["Backend Engineer", "AI Engineer"],
    }).raise_for_status()

    # resume upload + wait for processing
    response = client.post(
        "/api/resumes/upload", headers=headers,
        files={"file": ("sample_resume.docx", build_docx(),
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"title": "Demo Resume"},
    )
    response.raise_for_status()
    resume_id = response.json()["id"]
    for _ in range(30):
        detail = client.get(f"/api/resumes/{resume_id}", headers=headers).json()
        if detail["status"] in ("completed", "failed"):
            break
        time.sleep(1)
    if detail["status"] != "completed":
        print("Resume processing failed:", detail.get("error_message"))
        return 1
    print("[2/6] Resume uploaded and parsed")

    client.post(f"/api/resumes/{resume_id}/analyze", headers=headers).raise_for_status()
    print("[3/6] Resume analyzed")

    job_ids = []
    for path, title in (
        (SAMPLES / "job_backend_engineer.txt", "Backend Engineer"),
        (SAMPLES / "job_ai_engineer.txt", "AI Engineer"),
    ):
        response = client.post("/api/jobs/analyze", headers=headers, json={
            "title": title, "description": path.read_text(encoding="utf-8"),
        })
        response.raise_for_status()
        job_ids.append(response.json()["id"])
    print("[4/6] Two jobs analyzed")

    match = client.post(f"/api/jobs/{job_ids[0]}/match", headers=headers,
                        json={"resume_id": resume_id})
    match.raise_for_status()
    client.post(f"/api/skills/gaps/{resume_id}/{job_ids[0]}",
                headers=headers).raise_for_status()
    print(f"[5/6] Match computed: {match.json()['overall_score']}% + skill gaps")

    client.post("/api/applications", headers=headers, json={
        "company": "TechCo", "job_title": "Backend Engineer",
        "status": "applied", "location": "Remote", "job_id": job_ids[0],
        "resume_id": resume_id,
    }).raise_for_status()
    print("[6/6] Application tracked")

    print(f"\nDone. Log in at http://localhost:3000 with {DEMO_EMAIL} / {DEMO_PASSWORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
