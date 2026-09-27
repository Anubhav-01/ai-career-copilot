"""Hybrid job-description analysis: rule-based draft + LLM refinement,
followed by grounding against the JD text."""
import re
from collections import Counter

from app.ai.guardrails import call_structured
from app.ai.llm.base import LLMProvider
from app.ai.parsing.skills import extract_skills, is_known_skill
from app.ai.prompts import SYSTEMS, build_prompt
from app.core.errors import AIServiceError
from app.core.logging import get_logger
from app.schemas.job import JobAnalysis

logger = get_logger(__name__)

_REQUIRED_HINTS = ("required", "must have", "must-have", "requirements", "you have",
                   "we require", "qualifications", "you bring")
_PREFERRED_HINTS = ("preferred", "nice to have", "nice-to-have", "bonus", "plus",
                    "good to have", "desirable")
_YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE)
_SENIORITY = ("intern", "junior", "entry level", "entry-level", "mid-level",
              "senior", "staff", "principal", "lead")

_STOPWORDS = {
    "the", "and", "for", "with", "you", "our", "are", "will", "have", "that",
    "this", "your", "not", "all", "can", "who", "has", "was", "were", "been",
    "from", "into", "them", "they", "their", "there", "what", "when", "where",
    "which", "while", "would", "should", "could", "about", "above", "after",
    "team", "work", "working", "role", "job", "position", "company", "we",
    "us", "as", "an", "a", "of", "to", "in", "on", "or", "is", "be", "at",
    "by", "it", "its", "if", "more", "other", "such", "than", "also",
    "including", "etc", "experience", "years", "skills", "strong", "ability",
    "knowledge", "plus", "must", "required", "preferred", "responsibilities",
}


def _classify_skill_kinds(text: str) -> tuple[list[str], list[str]]:
    """Split detected skills into required vs preferred based on which
    section of the JD they appear in."""
    required: list[str] = []
    preferred: list[str] = []
    mode = "required"
    for line in text.splitlines():
        lowered = line.lower()
        if any(h in lowered for h in _PREFERRED_HINTS):
            mode = "preferred"
        elif any(h in lowered for h in _REQUIRED_HINTS):
            mode = "required"
        for skill in extract_skills(line):
            target = preferred if mode == "preferred" else required
            if skill.name not in target:
                target.append(skill.name)
    required_set = set(required)
    preferred = [s for s in preferred if s not in required_set]
    return required, preferred


def _keywords(text: str, limit: int = 15) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.]{2,}", text.lower())
    counts = Counter(w for w in words if w not in _STOPWORDS)
    return [w for w, _ in counts.most_common(limit)]


def _bullets_under(text: str, headers: tuple[str, ...]) -> list[str]:
    lines = text.splitlines()
    collecting = False
    out: list[str] = []
    for line in lines:
        lowered = line.strip().lower()
        if any(h in lowered for h in headers) and len(lowered) < 60:
            collecting = True
            continue
        if collecting:
            stripped = line.strip(" -•*\t")
            if not stripped:
                continue
            if len(stripped) < 60 and stripped.endswith(":"):
                collecting = False
                continue
            out.append(stripped)
            if len(out) >= 10:
                break
    return out


def deterministic_job_analysis(description: str, title: str | None = None,
                               company: str | None = None) -> JobAnalysis:
    required, preferred = _classify_skill_kinds(description)
    years_match = _YEARS_RE.search(description)
    lowered = description.lower()
    seniority = next((s for s in _SENIORITY if s in lowered), None)
    education = [
        line.strip(" -•*")
        for line in description.splitlines()
        if re.search(r"\b(bachelor|master|phd|b\.?s\.?c?|m\.?s\.?c?|degree)\b",
                     line, re.IGNORECASE)
    ][:3]

    return JobAnalysis(
        job_title=title or "",
        company=company or "",
        required_skills=required,
        preferred_skills=preferred,
        education=education,
        experience_years_min=int(years_match.group(1)) if years_match else None,
        responsibilities=_bullets_under(
            description, ("responsibilities", "what you'll do", "what you will do",
                          "your role", "the role")
        ),
        tools=[s for s in required + preferred if is_known_skill(s)][:15],
        technologies=[s for s in required + preferred][:20],
        keywords=_keywords(description),
        seniority=seniority,
    )


def analyze_job(description: str, llm: LLMProvider, title: str | None = None,
                company: str | None = None) -> JobAnalysis:
    draft = deterministic_job_analysis(description, title, company)
    prompt = build_prompt(
        instruction=(
            "Refine this job-description analysis draft using ONLY the raw job"
            " text. Correct the job title/company if stated, complete"
            " responsibilities, and reclassify required vs preferred skills"
            " if the draft got them wrong."
        ),
        context={"draft": draft.model_dump(), "raw_text": description[:12000]},
        schema_hint=(
            "JobAnalysis: job_title, company, required_skills[],"
            " preferred_skills[], education[], experience_years_min,"
            " responsibilities[], tools[], technologies[], keywords[], seniority"
        ),
    )
    try:
        refined = call_structured(
            llm, "job_analysis", SYSTEMS["job_analysis"], prompt, JobAnalysis,
            max_tokens=2000,
        )
    except AIServiceError:
        logger.warning("LLM refinement unavailable; using rule-based job analysis")
        return draft

    lowered = description.lower()
    refined.required_skills = [s for s in refined.required_skills if s.lower() in lowered]
    refined.preferred_skills = [s for s in refined.preferred_skills if s.lower() in lowered]
    if not refined.required_skills:
        refined.required_skills = draft.required_skills
    refined.keywords = refined.keywords or draft.keywords
    refined.job_title = refined.job_title or draft.job_title
    return refined
