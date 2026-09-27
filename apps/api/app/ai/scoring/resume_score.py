"""Resume scoring engine.

Overall score = weighted average of six documented components (weights are
configurable via RESUME_SCORE_WEIGHT_* environment variables, defaults in
app.core.config.ScoreWeights):

    25% ATS compatibility   - heuristic ATS-style checks
    20% Skills              - breadth/depth of recognized skills
    20% Experience quality  - entries, action verbs, quantified impact
    15% Projects            - presence and technical depth
    10% Keyword coverage    - alignment with target roles (or skill spread)
    10% Structure           - sections + contact completeness

Every component carries a human-readable explanation (explainability).
"""
from app.ai.parsing.skills import extract_skills
from app.ai.scoring.ats import EXPECTED_SECTIONS, action_verbs, analyze_ats
from app.core.config import get_settings
from app.schemas.analysis import ATSResult, Recommendation, ScoreComponent
from app.schemas.resume import ResumeExtraction


def _skills_score(extraction: ResumeExtraction, text: str) -> ScoreComponent:
    skills = extract_skills(text)
    categories = {s.category for s in skills}
    count_score = min(1.0, len(skills) / 12) * 70
    diversity_score = min(1.0, len(categories) / 4) * 30
    score = count_score + diversity_score
    return ScoreComponent(
        key="skills", label="Skills", score=round(score, 1),
        weight=get_settings().resume_score_weights.skills,
        explanation=f"{len(skills)} recognized skills across {len(categories)}"
                    f" categories. 12+ skills across 4+ categories scores full marks.",
    )


def _experience_score(extraction: ResumeExtraction) -> ScoreComponent:
    entries = extraction.experience
    if not entries:
        return ScoreComponent(
            key="experience", label="Experience Quality", score=0,
            weight=get_settings().resume_score_weights.experience,
            explanation="No structured experience entries were detected.",
        )
    bullets = [b for e in entries for b in e.bullets]
    verb_ratio = (
        sum(1 for b in bullets if b.split()[0].lower().rstrip(",.") in action_verbs())
        / len(bullets)
    ) if bullets else 0
    quant_ratio = (
        sum(1 for b in bullets if any(c.isdigit() for c in b)) / len(bullets)
    ) if bullets else 0
    dated = sum(1 for e in entries if e.start_date) / len(entries)
    score = (
        min(1.0, len(entries) / 3) * 30
        + verb_ratio * 30
        + quant_ratio * 25
        + dated * 15
    )
    return ScoreComponent(
        key="experience", label="Experience Quality", score=round(score, 1),
        weight=get_settings().resume_score_weights.experience,
        explanation=f"{len(entries)} experience entries; {round(verb_ratio * 100)}%"
                    f" of bullets lead with action verbs, {round(quant_ratio * 100)}%"
                    " include measurable results.",
    )


def _projects_score(extraction: ResumeExtraction) -> ScoreComponent:
    projects = extraction.projects
    if not projects:
        return ScoreComponent(
            key="projects", label="Projects", score=0,
            weight=get_settings().resume_score_weights.projects,
            explanation="No projects detected. Projects are strong evidence of"
                        " applied skills, especially for early-career roles.",
        )
    with_tech = sum(1 for p in projects if p.technologies) / len(projects)
    described = sum(1 for p in projects if len(p.description) > 40) / len(projects)
    score = min(1.0, len(projects) / 3) * 40 + with_tech * 30 + described * 30
    return ScoreComponent(
        key="projects", label="Projects", score=round(score, 1),
        weight=get_settings().resume_score_weights.projects,
        explanation=f"{len(projects)} projects; {round(with_tech * 100)}% list"
                    f" technologies and {round(described * 100)}% have substantive"
                    " descriptions.",
    )


def _keyword_score(text: str, target_roles: list[str]) -> ScoreComponent:
    skills = extract_skills(text)
    if target_roles:
        role_terms = {w.lower() for role in target_roles for w in role.split()}
        hits = sum(1 for s in skills if any(t in s.category for t in role_terms)
                   or any(t in s.name for t in role_terms))
        score = min(1.0, (hits + len(skills) / 15) / 2) * 100
        explanation = (f"Coverage estimated against your target roles"
                       f" ({', '.join(target_roles[:3])}).")
    else:
        sections_with_skills = len({s.evidence for s in skills})
        score = min(1.0, sections_with_skills / 10) * 100
        explanation = ("No target roles set - measured how widely skills are"
                       " evidenced across the resume. Set target roles in your"
                       " profile for a sharper signal.")
    return ScoreComponent(
        key="keyword_coverage", label="Keyword Coverage", score=round(score, 1),
        weight=get_settings().resume_score_weights.keyword_coverage,
        explanation=explanation,
    )


def _structure_score(ats: ATSResult, extraction: ResumeExtraction) -> ScoreComponent:
    section_ratio = 1 - len(ats.missing_sections) / len(EXPECTED_SECTIONS)
    contact = sum(1 for v in (extraction.email, extraction.phone, extraction.name) if v) / 3
    score = section_ratio * 60 + contact * 40
    return ScoreComponent(
        key="structure", label="Resume Structure", score=round(score, 1),
        weight=get_settings().resume_score_weights.structure,
        explanation=f"{len(EXPECTED_SECTIONS) - len(ats.missing_sections)} of"
                    f" {len(EXPECTED_SECTIONS)} core sections present;"
                    f" contact info {round(contact * 100)}% complete.",
    )


def compute_resume_score(
    text: str,
    extraction: ResumeExtraction,
    target_roles: list[str] | None = None,
) -> tuple[float, list[ScoreComponent], ATSResult, list[Recommendation]]:
    settings = get_settings()
    ats = analyze_ats(text, extraction)

    components = [
        ScoreComponent(
            key="ats", label="ATS Compatibility", score=round(ats.score, 1),
            weight=settings.resume_score_weights.ats,
            explanation="Heuristic ATS-style checks: sections, contact info,"
                        " bullets, action verbs, quantified impact, keyword use."
                        " (Simulated - not an actual proprietary ATS.)",
        ),
        _skills_score(extraction, text),
        _experience_score(extraction),
        _projects_score(extraction),
        _keyword_score(text, target_roles or []),
        _structure_score(ats, extraction),
    ]

    overall = round(sum(c.score * c.weight for c in components), 1)

    recommendations: list[Recommendation] = []
    for finding in ats.findings:
        recommendations.append(Recommendation(
            priority="high" if finding.severity == "critical" else "medium",
            category=finding.category,
            problem=finding.problem,
            recommendation=finding.recommendation,
        ))
    for component in sorted(components, key=lambda c: c.score)[:2]:
        if component.score < 60:
            recommendations.append(Recommendation(
                priority="high", category=component.key,
                problem=f"'{component.label}' is your weakest area"
                        f" ({component.score}/100).",
                recommendation=component.explanation,
            ))

    return overall, components, ats, recommendations
