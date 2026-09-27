"""Hybrid job-matching engine.

Final score = weighted blend (configurable via MATCH_WEIGHT_* env vars):

    40% semantic similarity (embeddings, resume chunks vs job chunks)
    25% required-skill coverage
    15% preferred-skill coverage
    10% experience fit
     5% education fit
     5% keyword overlap

Skill comparison is done on canonical taxonomy names. A "partial" match
means the resume has a different skill in the same category as the job
requirement (e.g. job wants Kubernetes, resume shows Docker).

Every skill judgment carries resume evidence for explainability.
"""
from dataclasses import dataclass

from app.ai.parsing.skills import normalize_skill, skill_category
from app.core.config import get_settings
from app.schemas.job import JobAnalysis
from app.schemas.match import MatchComponents, SkillEvidence


@dataclass
class ResumeSkillInfo:
    name: str
    category: str | None
    evidence: str | None


@dataclass
class MatchResult:
    overall: float
    components: MatchComponents
    strong_matches: list[str]
    partial_matches: list[str]
    missing_skills: list[str]
    evidence: list[SkillEvidence]
    weights: dict[str, float]


def calibrate_semantic(similarity: float) -> float:
    """Map raw cosine similarity to 0-100. Sentence-transformer cosine for
    related career documents typically lands in [0.15, 0.75]; scores are
    linearly calibrated over that band and clamped."""
    low, high = 0.15, 0.75
    scaled = (similarity - low) / (high - low)
    return round(max(0.0, min(1.0, scaled)) * 100, 1)


def _skill_coverage(
    job_skills: list[str], resume_skills: dict[str, ResumeSkillInfo]
) -> tuple[float, list[str], list[str], list[str]]:
    """Returns (score 0-100, strong, partial, missing)."""
    if not job_skills:
        return 100.0, [], [], []
    resume_categories = {
        info.category for info in resume_skills.values() if info.category
    }
    strong, partial, missing = [], [], []
    for skill in job_skills:
        canonical = normalize_skill(skill)
        if canonical in resume_skills:
            strong.append(canonical)
        elif skill_category(canonical) and skill_category(canonical) in resume_categories:
            partial.append(canonical)
        else:
            missing.append(canonical)
    score = (len(strong) + 0.4 * len(partial)) / len(job_skills) * 100
    return round(min(100.0, score), 1), strong, partial, missing


def _experience_fit(required_years: int | None, candidate_years: float | None) -> tuple[float, str]:
    if required_years is None:
        return 100.0, "The job does not state a minimum experience requirement."
    if candidate_years is None:
        return 50.0, (f"The job asks for {required_years}+ years but your"
                      " experience length could not be determined."
                      " Add dates to experience entries or set it in your profile.")
    if candidate_years >= required_years:
        return 100.0, f"You meet the {required_years}+ years requirement."
    ratio = candidate_years / required_years
    return round(ratio * 100, 1), (
        f"The job asks for {required_years}+ years; your resume/profile"
        f" indicates about {candidate_years:g}."
    )


def _education_fit(job_education: list[str], has_degree: bool) -> tuple[float, str]:
    if not job_education:
        return 100.0, "The job does not state education requirements."
    if has_degree:
        return 100.0, "Your resume lists a degree matching the education requirement."
    return 40.0, ("The job lists education requirements but no degree was"
                  " detected on your resume.")


def _keyword_overlap(job_keywords: list[str], resume_text: str) -> float:
    if not job_keywords:
        return 100.0
    lowered = resume_text.lower()
    hits = sum(1 for k in job_keywords if k.lower() in lowered)
    return round(hits / len(job_keywords) * 100, 1)


def compute_match(
    job_analysis: JobAnalysis,
    resume_skills: list[ResumeSkillInfo],
    resume_text: str,
    semantic_similarity: float,
    candidate_years: float | None,
    has_degree: bool,
) -> MatchResult:
    weights = get_settings().match_weights
    skill_index = {normalize_skill(s.name): s for s in resume_skills}

    required_score, strong_req, partial_req, missing_req = _skill_coverage(
        job_analysis.required_skills, skill_index
    )
    preferred_score, strong_pref, partial_pref, missing_pref = _skill_coverage(
        job_analysis.preferred_skills, skill_index
    )
    semantic_score = calibrate_semantic(semantic_similarity)
    experience_score, _ = _experience_fit(
        job_analysis.experience_years_min, candidate_years
    )
    education_score, _ = _education_fit(job_analysis.education, has_degree)
    keyword_score = _keyword_overlap(job_analysis.keywords, resume_text)

    components = MatchComponents(
        semantic=semantic_score,
        required_skills=required_score,
        preferred_skills=preferred_score,
        experience=experience_score,
        education=education_score,
        keywords=keyword_score,
    )
    overall = round(
        components.semantic * weights.semantic
        + components.required_skills * weights.required_skills
        + components.preferred_skills * weights.preferred_skills
        + components.experience * weights.experience
        + components.education * weights.education
        + components.keywords * weights.keywords,
        1,
    )

    strong = list(dict.fromkeys(strong_req + strong_pref))
    partial = list(dict.fromkeys(partial_req + partial_pref))
    missing = list(dict.fromkeys(missing_req + missing_pref))
    evidence = [
        SkillEvidence(skill=s, evidence=skill_index[s].evidence or "", section=None)
        for s in strong
        if s in skill_index and skill_index[s].evidence
    ]

    return MatchResult(
        overall=overall,
        components=components,
        strong_matches=strong,
        partial_matches=partial,
        missing_skills=missing,
        evidence=evidence,
        weights=weights.model_dump(),
    )
