from app.ai.llm.mock_provider import MockProvider
from app.ai.parsing.resume_parser import (
    deterministic_extract,
    parse_resume,
    split_sections,
)
from tests.conftest import SAMPLE_RESUME_LINES

SAMPLE_TEXT = "\n".join(SAMPLE_RESUME_LINES)


def test_section_splitting():
    sections = split_sections(SAMPLE_TEXT)
    for expected in ("summary", "skills", "experience", "projects", "education"):
        assert expected in sections, f"missing section {expected}"
    assert "FastAPI" in sections["experience"]


def test_contact_extraction():
    extraction = deterministic_extract(SAMPLE_TEXT)
    assert extraction.email == "alex.morgan@example.com"
    assert extraction.phone is not None
    assert any("github.com" in link for link in extraction.links)


def test_skills_grounded_in_text():
    extraction = deterministic_extract(SAMPLE_TEXT)
    assert "python" in extraction.skills
    assert "fastapi" in extraction.skills
    # nothing invented
    lowered = SAMPLE_TEXT.lower()
    for skill in extraction.skills:
        assert skill.lower() in lowered or skill in ("rest apis", "ci/cd", "vector search"), skill


def test_hybrid_parse_with_mock_llm():
    extraction = parse_resume(SAMPLE_TEXT, MockProvider())
    assert extraction.email == "alex.morgan@example.com"
    assert "postgresql" in extraction.skills


def test_grounding_drops_hallucinated_content():
    from app.ai.parsing.resume_parser import _ground
    from app.schemas.resume import ExperienceItem, ResumeExtraction

    fake = ResumeExtraction(
        skills=["python", "quantum computing"],
        experience=[
            ExperienceItem(title="Software Engineer", company="Acme Corp"),
            ExperienceItem(title="CTO", company="Totally Invented Inc"),
        ],
        certifications=["AWS Solutions Architect"],
    )
    grounded = _ground(fake, SAMPLE_TEXT)
    assert "quantum computing" not in grounded.skills
    assert all(e.company != "Totally Invented Inc" for e in grounded.experience)
    assert grounded.certifications == []
