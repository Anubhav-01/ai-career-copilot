from tests.conftest import upload_sample_resume


def test_application_crud(client, auth_headers):
    created = client.post("/api/applications", headers=auth_headers, json={
        "company": "TechCo", "job_title": "Backend Engineer",
        "status": "saved", "location": "Remote",
    })
    assert created.status_code == 201
    application_id = created.json()["id"]

    updated = client.put(f"/api/applications/{application_id}",
                         headers=auth_headers,
                         json={"status": "applied", "notes": "Sent via referral"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "applied"

    invalid = client.put(f"/api/applications/{application_id}",
                         headers=auth_headers, json={"status": "ghosted"})
    assert invalid.status_code == 422

    listed = client.get("/api/applications", headers=auth_headers).json()
    assert any(a["id"] == application_id for a in listed)

    deleted = client.delete(f"/api/applications/{application_id}",
                            headers=auth_headers)
    assert deleted.status_code == 200
    listed = client.get("/api/applications", headers=auth_headers).json()
    assert all(a["id"] != application_id for a in listed)


def test_dashboard_aggregates(client, auth_headers):
    upload_sample_resume(client, auth_headers)
    client.post("/api/applications", headers=auth_headers, json={
        "company": "A", "job_title": "Engineer", "status": "applied",
    })
    client.post("/api/applications", headers=auth_headers, json={
        "company": "B", "job_title": "Engineer", "status": "interview",
    })

    dashboard = client.get("/api/dashboard", headers=auth_headers).json()
    assert dashboard["resume_count"] == 1
    assert dashboard["application_count"] == 2
    assert dashboard["profile_completeness"] > 0
    top_skills = [s["skill"] for s in dashboard["top_skills"]]
    assert "python" in top_skills
    funnel = {f["status"]: f["count"] for f in dashboard["application_funnel"]}
    assert funnel["applied"] == 1
    assert funnel["interview"] == 1


def test_profile_update_and_dashboard_cache_invalidation(client, auth_headers):
    profile = client.put("/api/profile", headers=auth_headers, json={
        "headline": "Backend engineer", "location": "Berlin",
        "target_roles": ["Backend Engineer", "AI Engineer"],
        "experience_years": 3,
    })
    assert profile.status_code == 200
    assert profile.json()["target_roles"] == ["Backend Engineer", "AI Engineer"]

    fetched = client.get("/api/profile", headers=auth_headers).json()
    assert fetched["headline"] == "Backend engineer"
