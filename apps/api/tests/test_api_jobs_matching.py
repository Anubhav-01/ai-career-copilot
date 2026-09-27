from tests.conftest import create_sample_job, upload_sample_resume


def test_job_analysis(client, auth_headers):
    job_id = create_sample_job(client, auth_headers)
    detail = client.get(f"/api/jobs/{job_id}", headers=auth_headers).json()
    analysis = detail["analysis"]
    required = [s.lower() for s in analysis["required_skills"]]
    assert "python" in required
    assert "postgresql" in required
    preferred = [s.lower() for s in analysis["preferred_skills"]]
    assert "kubernetes" in preferred
    assert analysis["experience_years_min"] == 2
    assert analysis["keywords"]


def test_job_description_too_short(client, auth_headers):
    response = client.post("/api/jobs/analyze", headers=auth_headers,
                           json={"description": "too short"})
    assert response.status_code == 422


def test_match_with_explainability(client, auth_headers):
    resume_id = upload_sample_resume(client, auth_headers)
    job_id = create_sample_job(client, auth_headers)

    response = client.post(f"/api/jobs/{job_id}/match", headers=auth_headers,
                           json={"resume_id": resume_id})
    assert response.status_code == 200, response.text
    match = response.json()

    assert 0 <= match["overall_score"] <= 100
    assert set(match["components"].keys()) == {
        "semantic", "required_skills", "preferred_skills", "experience",
        "education", "keywords",
    }
    strong = [s.lower() for s in match["strong_matches"]]
    assert "python" in strong
    assert "fastapi" in strong
    # Terraform is not on the resume: with other cloud_devops skills present
    # it is a partial (same-category) match, never a strong one.
    partial_or_missing = [
        s.lower() for s in match["partial_matches"] + match["missing_skills"]
    ]
    assert "terraform" in partial_or_missing
    assert "terraform" not in strong
    assert match["evidence"], "strong matches must carry resume evidence"
    assert match["explanation"]
    assert match["weights"]["semantic"] == 0.4

    # latest match endpoint
    latest = client.get(f"/api/jobs/{job_id}/match/{resume_id}",
                        headers=auth_headers).json()
    assert latest["id"] == match["id"]


def test_skill_gaps_and_roadmap(client, auth_headers):
    resume_id = upload_sample_resume(client, auth_headers)
    job_id = create_sample_job(client, auth_headers)

    gaps = client.post(f"/api/skills/gaps/{resume_id}/{job_id}",
                       headers=auth_headers).json()
    assert gaps
    by_skill = {g["normalized"]: g for g in gaps}
    assert "terraform" in by_skill
    assert by_skill["terraform"]["priority"] in ("critical", "important", "nice_to_have")
    assert all(g["reason"] for g in gaps)
    # resume already has python: never reported as a gap
    assert "python" not in by_skill

    # roadmap for the first gap
    gap_id = gaps[0]["id"]
    roadmap = client.post(f"/api/learning/roadmaps/{gap_id}",
                          headers=auth_headers)
    assert roadmap.status_code == 201, roadmap.text
    content = roadmap.json()["content"]
    assert content["stages"]
    assert all(s["practice_task"] for s in content["stages"])
    assert "http" not in str(content).lower()  # no fabricated URLs

    listed = client.get("/api/learning/roadmaps", headers=auth_headers).json()
    assert len(listed) >= 1


def test_skills_endpoint_lists_unique_skills(client, auth_headers):
    upload_sample_resume(client, auth_headers)
    skills = client.get("/api/skills", headers=auth_headers).json()
    normalized = [s["normalized"] for s in skills]
    assert len(normalized) == len(set(normalized))
    assert "python" in normalized
