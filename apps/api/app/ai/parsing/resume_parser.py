"""Hybrid resume parsing: deterministic extraction first, optional LLM
refinement second, then a grounding pass that drops anything the model
returned that is not literally supported by the resume text.

Pipeline:
    raw text
      -> contact info (regex + optional spaCy NER)
      -> section segmentation (header heuristics)
      -> taxonomy skill extraction (with evidence)
      -> draft ResumeExtraction
      -> LLM refinement (draft + raw text as ground truth)
      -> grounding filter (anti-hallucination)
"""
import re

from app.ai.guardrails import call_structured
from app.ai.llm.base import LLMProvider
from app.ai.parsing.skills import extract_skills
from app.ai.prompts import SYSTEMS, build_prompt
from app.core.errors import AIServiceError
from app.core.logging import get_logger
from app.schemas.resume import ResumeExtraction

logger = get_logger(__name__)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}")
URL_RE = re.compile(r"(?:https?://|www\.)[^\s|,;)]+|(?:github\.com|linkedin\.com)/[^\s|,;)]+")

SECTION_HEADERS: dict[str, list[str]] = {
    "summary": ["summary", "professional summary", "profile", "about", "objective"],
    "experience": ["experience", "work experience", "professional experience",
                   "employment", "employment history", "work history"],
    "education": ["education", "academic background", "academics"],
    "skills": ["skills", "technical skills", "core skills", "technologies",
               "skills & tools", "tech stack"],
    "projects": ["projects", "personal projects", "key projects", "selected projects"],
    "certifications": ["certifications", "certificates", "licenses"],
    "achievements": ["achievements", "awards", "honors", "accomplishments"],
}

_HEADER_LOOKUP = {
    alias: section for section, aliases in SECTION_HEADERS.items() for alias in aliases
}


def _is_header(line: str) -> str | None:
    cleaned = re.sub(r"[^a-z& ]", "", line.strip().lower()).strip()
    return _HEADER_LOOKUP.get(cleaned)


def split_sections(text: str) -> dict[str, str]:
    """Segment the resume into named sections using header heuristics."""
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in text.splitlines():
        detected = _is_header(line)
        if detected:
            current = detected
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}


def _extract_name(text: str, email: str | None) -> str | None:
    """Heuristic: first short, non-contact line of the document; refined by
    spaCy PERSON entities when available."""
    candidate = None
    for line in text.splitlines()[:5]:
        stripped = line.strip()
        if not stripped or _is_header(stripped):
            continue
        if EMAIL_RE.search(stripped) or URL_RE.search(stripped) or PHONE_RE.search(stripped):
            continue
        if 2 <= len(stripped.split()) <= 5 and len(stripped) < 60:
            candidate = stripped
            break
    try:
        import spacy

        nlp = _get_spacy(spacy)
        if nlp is not None:
            doc = nlp("\n".join(text.splitlines()[:10]))
            people = [e.text.strip() for e in doc.ents if e.label_ == "PERSON"]
            if people:
                return people[0]
    except ImportError:
        pass
    if candidate is None and email:
        return None
    return candidate


_spacy_nlp = None
_spacy_tried = False


def _get_spacy(spacy_module):
    global _spacy_nlp, _spacy_tried
    if not _spacy_tried:
        _spacy_tried = True
        try:
            _spacy_nlp = spacy_module.load("en_core_web_sm")
        except OSError:
            _spacy_nlp = None
    return _spacy_nlp


_BULLET_RE = re.compile(r"^\s*[-•*▪◦‣·]\s*")


def _bullets(block: str) -> list[str]:
    out = []
    for line in block.splitlines():
        if _BULLET_RE.match(line):
            out.append(_BULLET_RE.sub("", line).strip())
    return out


def deterministic_extract(text: str) -> ResumeExtraction:
    """Rule-based extraction (no LLM). Always runs; forms the trusted draft."""
    sections = split_sections(text)
    email_match = EMAIL_RE.search(text)
    email = email_match.group(0) if email_match else None
    phone_match = PHONE_RE.search(text)
    links = list(dict.fromkeys(URL_RE.findall(text)))
    skills = [s.name for s in extract_skills(text)]

    achievements = _bullets(sections.get("achievements", ""))
    certifications = [
        line.strip(" -•*")
        for line in sections.get("certifications", "").splitlines()
        if line.strip(" -•*")
    ]

    return ResumeExtraction(
        name=_extract_name(text, email),
        email=email,
        phone=phone_match.group(0) if phone_match else None,
        summary=sections.get("summary") or None,
        skills=skills,
        certifications=certifications,
        achievements=achievements,
        links=links,
    )


def _ground(extraction: ResumeExtraction, raw_text: str) -> ResumeExtraction:
    """Drop any LLM-added value not literally present in the resume text."""
    lowered = raw_text.lower()

    def supported(value: str | None) -> bool:
        """Word-boundary match so 'CTO' cannot match inside 'vector'."""
        if not value:
            return False
        return re.search(rf"(?<!\w){re.escape(value.lower())}(?!\w)", lowered) is not None

    extraction.skills = [s for s in extraction.skills if s.lower() in lowered]
    extraction.experience = [
        e for e in extraction.experience
        if supported(e.company) or supported(e.title)
    ]
    for item in extraction.experience:
        item.bullets = [b for b in item.bullets if b.lower()[:60] in lowered]
    extraction.education = [
        e for e in extraction.education
        if supported(e.institution) or supported(e.degree)
    ]
    extraction.projects = [p for p in extraction.projects if supported(p.name)]
    for project in extraction.projects:
        project.technologies = [t for t in project.technologies if t.lower() in lowered]
    extraction.certifications = [c for c in extraction.certifications if supported(c)]
    extraction.achievements = [a for a in extraction.achievements if a.lower()[:60] in lowered]
    if extraction.email and extraction.email.lower() not in lowered:
        extraction.email = None
    return extraction


def parse_resume(text: str, llm: LLMProvider) -> ResumeExtraction:
    """Full hybrid pipeline. Falls back to the deterministic draft if the
    LLM is unavailable."""
    draft = deterministic_extract(text)
    prompt = build_prompt(
        instruction=(
            "Refine this resume extraction draft. Fill in experience entries"
            " (title, company, dates, bullets), education, projects and"
            " location using ONLY the raw resume text. Keep every draft field"
            " that is already correct."
        ),
        context={"draft": draft.model_dump(), "raw_text": text[:12000]},
        schema_hint=ResumeExtraction.model_json_schema()["title"]
        + ": name, email, phone, location, summary, skills[], experience[],"
        " education[], projects[], certifications[], achievements[], links[]",
    )
    try:
        refined = call_structured(
            llm, "resume_extraction", SYSTEMS["resume_extraction"], prompt,
            ResumeExtraction, max_tokens=2500,
        )
    except AIServiceError:
        logger.warning("LLM refinement unavailable; using deterministic draft")
        return draft

    # Merge: deterministic contact fields win when present (regex > LLM).
    refined.email = draft.email or refined.email
    refined.phone = draft.phone or refined.phone
    refined.links = draft.links or refined.links
    refined.name = refined.name or draft.name
    refined.summary = refined.summary or draft.summary
    merged_skills = list(dict.fromkeys([*draft.skills, *refined.skills]))
    refined.skills = merged_skills
    refined.certifications = refined.certifications or draft.certifications
    refined.achievements = refined.achievements or draft.achievements
    return _ground(refined, text)
