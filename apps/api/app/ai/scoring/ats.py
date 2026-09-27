"""ATS-style analysis (deterministic heuristics, no LLM cost).

IMPORTANT: this simulates common applicant-tracking-system checks for
guidance. It does not claim to reproduce any proprietary ATS.
"""
import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from app.ai.parsing.resume_parser import EMAIL_RE, PHONE_RE, split_sections
from app.ai.parsing.skills import extract_skills
from app.schemas.analysis import ATSFinding, ATSResult
from app.schemas.resume import ResumeExtraction

_VERBS_PATH = Path(__file__).resolve().parents[2] / "data" / "action_verbs.json"

EXPECTED_SECTIONS = ["summary", "experience", "education", "skills"]
OPTIONAL_SECTIONS = ["projects", "certifications", "achievements"]

_BULLET_RE = re.compile(r"^\s*[-•*▪◦‣·]\s*(.+)$", re.MULTILINE)
_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?\s*(?:%|percent|x|k|m|users|ms|s\b)?", re.IGNORECASE)


@lru_cache
def action_verbs() -> frozenset[str]:
    with open(_VERBS_PATH, encoding="utf-8") as f:
        return frozenset(json.load(f))


def _bullets(text: str) -> list[str]:
    return [m.strip() for m in _BULLET_RE.findall(text)]


def analyze_ats(text: str, extraction: ResumeExtraction) -> ATSResult:
    findings: list[ATSFinding] = []
    sections = split_sections(text)
    detected = [s for s in EXPECTED_SECTIONS + OPTIONAL_SECTIONS if s in sections]
    missing = [s for s in EXPECTED_SECTIONS if s not in sections]

    score = 100.0

    for section in missing:
        score -= 10
        findings.append(ATSFinding(
            severity="critical", category="sections",
            problem=f"No '{section}' section was detected.",
            recommendation=f"Add a clearly-labeled '{section.title()}' section"
                           " with a standard heading so parsers can find it.",
        ))

    # Contact info
    if not EMAIL_RE.search(text):
        score -= 10
        findings.append(ATSFinding(
            severity="critical", category="contact",
            problem="No email address found.",
            recommendation="Add a professional email address near the top.",
        ))
    if not PHONE_RE.search(text):
        score -= 4
        findings.append(ATSFinding(
            severity="warning", category="contact",
            problem="No phone number found.",
            recommendation="Add a phone number so recruiters can reach you.",
        ))

    # Action verbs & quantification
    bullets = _bullets(text)
    verb_hits = sum(
        1 for b in bullets if b.split()[0].lower().rstrip(",.") in action_verbs()
    ) if bullets else 0
    quantified = sum(1 for b in bullets if _NUMBER_RE.search(b)) if bullets else 0
    quantified_ratio = quantified / len(bullets) if bullets else 0.0

    if not bullets:
        score -= 8
        findings.append(ATSFinding(
            severity="warning", category="formatting",
            problem="No bullet points detected.",
            recommendation="Describe experience with concise bullet points"
                           " instead of paragraphs.",
        ))
    else:
        if verb_hits / len(bullets) < 0.5:
            score -= 6
            findings.append(ATSFinding(
                severity="warning", category="impact",
                problem="Fewer than half of your bullets start with a strong action verb.",
                recommendation="Start bullets with verbs such as 'Built',"
                               " 'Implemented', 'Reduced', 'Led'.",
            ))
        if quantified_ratio < 0.3:
            score -= 8
            findings.append(ATSFinding(
                severity="warning", category="impact",
                problem=f"Only {round(quantified_ratio * 100)}% of bullets contain"
                        " a measurable result.",
                recommendation="Where you have real numbers (users, latency,"
                               " revenue, time saved), add them. Do not invent"
                               " metrics you cannot back up.",
            ))

    # Keyword stuffing
    skill_names = [s.name for s in extract_skills(text)]
    word_counts = Counter(re.findall(r"[a-zA-Z+#.]{3,}", text.lower()))
    stuffing = any(word_counts.get(s.lower(), 0) > 12 for s in skill_names)
    if stuffing:
        score -= 8
        findings.append(ATSFinding(
            severity="warning", category="keywords",
            problem="Some skills are repeated so often it may read as keyword stuffing.",
            recommendation="Mention each skill where it matters (skills section"
                           " plus 1-2 evidence bullets), not on every line.",
        ))

    if not skill_names:
        score -= 10
        findings.append(ATSFinding(
            severity="critical", category="keywords",
            problem="No recognizable technical skills were detected.",
            recommendation="Add a skills section listing concrete tools and"
                           " technologies you have used.",
        ))

    # Length
    word_count = len(text.split())
    if word_count < 150:
        score -= 8
        findings.append(ATSFinding(
            severity="warning", category="formatting",
            problem=f"Resume is very short ({word_count} words).",
            recommendation="Expand experience and project descriptions with"
                           " specific responsibilities and outcomes.",
        ))
    elif word_count > 1200:
        score -= 4
        findings.append(ATSFinding(
            severity="info", category="formatting",
            problem=f"Resume is long ({word_count} words).",
            recommendation="Aim for 1-2 pages; trim older or less relevant items.",
        ))

    if extraction.summary is None:
        score -= 3
        findings.append(ATSFinding(
            severity="info", category="sections",
            problem="No professional summary detected.",
            recommendation="Add a 2-3 line summary targeting your desired role.",
        ))

    return ATSResult(
        score=max(0.0, min(100.0, score)),
        findings=findings,
        action_verb_count=verb_hits,
        quantified_bullet_ratio=round(quantified_ratio, 3),
        detected_sections=detected,
        missing_sections=missing,
        keyword_stuffing_detected=stuffing,
    )
