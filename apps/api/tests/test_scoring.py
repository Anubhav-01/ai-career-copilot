import pytest

from app.ai.parsing.resume_parser import deterministic_extract
from app.ai.scoring.ats import analyze_ats
from app.ai.scoring.match_score import (
    ResumeSkillInfo,
    calibrate_semantic,
    compute_match,
)
from app.ai.scoring.resume_score import compute_resume_score
from app.schemas.job import JobAnalysis
from tests.conftest import SAMPLE_RESUME_LINES

SAMPLE_TEXT = "\n".join(SAMPLE_RESUME_LINES)


def test_ats_detects_missing_sections():
    result = analyze_ats("just some text with python", deterministic_extract("python"))
    assert result.score < 70
    assert "experience" in result.missing_sections
    assert any(f.severity == "critical" for f in result.findings)


def test_ats_good_resume_scores_high():
    extraction = deterministic_extract(SAMPLE_TEXT)
    result = analyze_ats(SAMPLE_TEXT, extraction)
    assert result.score >= 60
    assert result.missing_sections == []
    assert result.quantified_bullet_ratio > 0


def test_resume_score_weighted_average():
    extraction = deterministic_extract(SAMPLE_TEXT)
    overall, components, ats, recommendations = compute_resume_score(
        SAMPLE_TEXT, extraction
    )
    assert 0 <= overall <= 100
    weights = sum(c.weight for c in components)
    assert weights == pytest.approx(1.0)
    expected = sum(c.score * c.weight for c in components)
    assert overall == pytest.approx(expected, abs=0.11)
    assert all(c.explanation for c in components)  # explainability


def test_semantic_calibration_bounds():
    assert calibrate_semantic(0.0) == 0.0
    assert calibrate_semantic(0.9) == 100.0
    assert 0 < calibrate_semantic(0.45) < 100


def _match(required, preferred, resume_skills):
    analysis = JobAnalysis(
        required_skills=required, preferred_skills=preferred,
        keywords=["python"], experience_years_min=2,
    )
    infos = [ResumeSkillInfo(name=s, category=None, evidence=f"used {s}")
             for s in resume_skills]
    return compute_match(
        job_analysis=analysis, resume_skills=infos,
        resume_text=" ".join(resume_skills) + " python",
        semantic_similarity=0.5, candidate_years=3.0, has_degree=True,
    )


def test_match_full_required_coverage():
    result = _match(["python", "docker"], [], ["python", "docker"])
    assert result.components.required_skills == 100.0
    assert set(result.strong_matches) == {"python", "docker"}
    assert result.missing_skills == []
    assert all(e.evidence for e in result.evidence)  # evidence attached


def test_match_missing_and_partial():
    # resume has docker (cloud_devops) but job wants kubernetes -> partial
    from app.ai.parsing.skills import skill_category

    infos = [ResumeSkillInfo(name="docker", category=skill_category("docker"),
                             evidence="Deployed with Docker")]
    analysis = JobAnalysis(required_skills=["kubernetes"], keywords=[])
    result = compute_match(
        job_analysis=analysis, resume_skills=infos, resume_text="docker",
        semantic_similarity=0.4, candidate_years=None, has_degree=False,
    )
    assert "kubernetes" in result.partial_matches
    assert result.components.required_skills == pytest.approx(40.0)


def test_match_score_within_bounds_and_explainable():
    result = _match(["python", "terraform"], ["redis"], ["python"])
    assert 0 <= result.overall <= 100
    assert "terraform" in result.missing_skills
    assert result.weights["semantic"] == pytest.approx(0.40)
