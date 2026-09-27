from tests.conftest import create_sample_job, upload_sample_resume

GOOD_ANSWER = (
    "In my last project I built REST APIs with FastAPI because it offers"
    " async support, automatic OpenAPI docs and Pydantic validation. First I"
    " designed the resource model, then I structured the app into routers,"
    " services and repositories. As a result the API served about 10k"
    " requests per day with p95 latency under 200ms. For example, I moved"
    " heavy parsing into background tasks to keep endpoints fast."
)


def _create_interview(client, headers, **overrides):
    resume_id = upload_sample_resume(client, headers)
    job_id = create_sample_job(client, headers)
    payload = {
        "target_role": "Backend Engineer",
        "resume_id": resume_id,
        "job_id": job_id,
        "difficulty": "medium",
        "mode": "mock",
        "question_count": 4,
        **overrides,
    }
    response = client.post("/api/interviews", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_questions_are_grounded(client, auth_headers):
    interview = _create_interview(client, auth_headers)
    questions = interview["questions"]
    assert len(questions) == 4
    assert all(q["question"] for q in questions)
    # At least one question must be grounded in actual resume/job content.
    groundings = " ".join(q.get("grounding") or "" for q in questions).lower()
    assert any(term in groundings for term in ("python", "fastapi", "resume", "job"))


def test_mock_interview_loop_and_report(client, auth_headers):
    interview = _create_interview(client, auth_headers)
    interview_id = interview["id"]
    questions = interview["questions"]

    completed = False
    for question in questions:
        response = client.post(
            f"/api/interviews/{interview_id}/answer", headers=auth_headers,
            json={"question_id": question["id"], "answer": GOOD_ANSWER},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        feedback = body["feedback"]
        assert 0 <= feedback["score"] <= 100
        assert feedback["strengths"]
        assert feedback["suggested_structure"]
        completed = body["interview_completed"]

    assert completed

    report = client.get(f"/api/interviews/{interview_id}/report",
                        headers=auth_headers).json()
    assert report["answered"] == 4
    assert report["total_questions"] == 4
    assert 0 <= report["overall_score"] <= 100
    assert report["category_scores"]


def test_cannot_answer_same_question_twice(client, auth_headers):
    interview = _create_interview(client, auth_headers)
    question_id = interview["questions"][0]["id"]
    url = f"/api/interviews/{interview['id']}/answer"

    first = client.post(url, headers=auth_headers,
                        json={"question_id": question_id, "answer": GOOD_ANSWER})
    assert first.status_code == 200
    second = client.post(url, headers=auth_headers,
                         json={"question_id": question_id, "answer": GOOD_ANSWER})
    assert second.status_code == 422


def test_interview_without_resume(client, auth_headers):
    response = client.post("/api/interviews", headers=auth_headers, json={
        "target_role": "Data Engineer", "question_count": 3,
    })
    assert response.status_code == 201
    assert len(response.json()["questions"]) == 3
