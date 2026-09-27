"""Prompt templates.

Every prompt embeds a machine-readable CONTEXT block (JSON between
markers). This keeps prompts consistent, lets the MockProvider produce
grounded deterministic output, and makes anti-hallucination rules explicit
for real LLMs.
"""
import json
from typing import Any

CONTEXT_START = "<<CONTEXT_JSON>>"
CONTEXT_END = "<<END_CONTEXT_JSON>>"

ANTI_HALLUCINATION = (
    "STRICT RULES:\n"
    "- Use ONLY information present in the provided context.\n"
    "- NEVER invent employers, dates, metrics, technologies, certifications,"
    " achievements or responsibilities.\n"
    "- If information is missing, leave the field empty instead of guessing.\n"
    "- Output MUST be a single valid JSON object matching the requested schema.\n"
)


def build_prompt(instruction: str, context: dict[str, Any], schema_hint: str) -> str:
    return (
        f"{instruction}\n\n"
        f"{ANTI_HALLUCINATION}\n"
        f"JSON schema of the expected output:\n{schema_hint}\n\n"
        f"{CONTEXT_START}\n{json.dumps(context, ensure_ascii=False, default=str)}\n{CONTEXT_END}"
    )


def extract_context(prompt: str) -> dict[str, Any]:
    """Used by MockProvider to recover the structured context."""
    try:
        start = prompt.index(CONTEXT_START) + len(CONTEXT_START)
        end = prompt.index(CONTEXT_END)
        return json.loads(prompt[start:end].strip())
    except (ValueError, json.JSONDecodeError):
        return {}


SYSTEMS = {
    "resume_extraction": (
        "You are a precise resume parser. You refine a draft extraction produced"
        " by deterministic parsing, using the raw resume text as ground truth."
    ),
    "job_analysis": (
        "You are a precise job-description analyst. You refine a draft analysis"
        " produced by rule-based parsing, using the raw job text as ground truth."
    ),
    "resume_explanation": (
        "You are a career coach. You explain resume scores in plain language,"
        " grounded only in the provided findings."
    ),
    "bullet_improvement": (
        "You improve resume bullet wording. You keep all facts identical and"
        " never add metrics, tools or outcomes that are not in the original."
    ),
    "tailoring": (
        "You suggest how to tailor a resume to a job. You only reference skills"
        " and evidence that actually appear in the resume."
    ),
    "match_explanation": (
        "You explain job-match scores in plain language, grounded only in the"
        " provided component scores and skill lists."
    ),
    "interview_questions": (
        "You are an experienced technical interviewer. You generate questions"
        " grounded in the candidate's actual resume content and the target job."
    ),
    "interview_feedback": (
        "You evaluate interview answers on relevance, technical correctness,"
        " clarity, completeness and structure. You judge only the text of the"
        " answer and make no personality or psychological claims."
    ),
    "learning_roadmap": (
        "You design practical multi-week learning roadmaps for a single skill."
        " You never fabricate course URLs or brand names."
    ),
}
