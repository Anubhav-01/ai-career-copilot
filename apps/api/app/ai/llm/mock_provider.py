"""Deterministic mock LLM provider.

Lets the whole product run end-to-end without an API key (development,
tests, demos). Outputs are derived only from the structured context that
prompts embed, so behavior stays grounded rather than fabricated. It is
clearly labeled as a mock in docs; production should use a real provider.
"""
import json
from typing import Any

from app.ai.llm.base import LLMProvider, LLMRequest
from app.ai.prompts import extract_context

_ACTION_VERBS = ("developed", "built", "designed", "implemented", "led", "created")

_STRUCTURE_MARKERS = (
    "first", "then", "finally", "because", "for example", "as a result",
    "situation", "task", "action", "result", "step",
)


class MockProvider(LLMProvider):
    name = "mock"

    def generate(self, request: LLMRequest) -> str:
        context = extract_context(request.prompt)
        handler = getattr(self, f"_{request.task}", None)
        result: dict[str, Any] = handler(context) if handler else {}
        return json.dumps(result, ensure_ascii=False)

    # --- task handlers -------------------------------------------------

    @staticmethod
    def _resume_extraction(ctx: dict) -> dict:
        # Echo the deterministic draft; real LLMs would refine it.
        return ctx.get("draft", {})

    @staticmethod
    def _job_analysis(ctx: dict) -> dict:
        return ctx.get("draft", {})

    @staticmethod
    def _resume_explanation(ctx: dict) -> dict:
        scores = ctx.get("scores", [])
        parts = [
            f"{s.get('label')}: {round(float(s.get('score', 0)))}/100 (weight {int(float(s.get('weight', 0)) * 100)}%)"
            for s in scores
        ]
        weakest = min(scores, key=lambda s: float(s.get("score", 0)), default=None)
        text = "Your overall score is a weighted average of: " + "; ".join(parts) + "."
        if weakest:
            text += (
                f" The biggest opportunity is '{weakest.get('label')}'"
                f" - see the recommendations for concrete fixes."
            )
        return {"explanation": text}

    @staticmethod
    def _bullet_improvement(ctx: dict) -> dict:
        original: str = ctx.get("bullet", "").strip().rstrip(".")
        lowered = original.lower()
        improved = original
        if not any(lowered.startswith(v) for v in _ACTION_VERBS):
            improved = f"Developed {original[0].lower()}{original[1:]}" if original else original
        improved = improved.rstrip(".") + "."
        has_number = any(ch.isdigit() for ch in original)
        return {
            "original": ctx.get("bullet", ""),
            "improved": improved,
            "rationale": (
                "Rephrased to lead with an action verb while keeping every fact"
                " from the original bullet unchanged."
            ),
            "missing_metric_suggestion": None
            if has_number
            else (
                "If you can measure the outcome (users, latency, revenue, time"
                " saved), add a real number - do not estimate one."
            ),
        }

    @staticmethod
    def _tailoring(ctx: dict) -> dict:
        matched = ctx.get("matched_skills", [])
        missing = ctx.get("missing_skills", [])
        keywords = ctx.get("job_keywords", [])
        return {
            "skills_to_emphasize": matched[:8],
            "keywords_to_include": [k for k in keywords if k.lower() in
                                    {m.lower() for m in matched}][:8],
            "sections_to_modify": ["summary", "skills"] + (["experience"] if matched else []),
            "bullets_to_improve": ctx.get("weak_bullets", [])[:5],
            "missing_evidence": [
                f"The job asks for '{s}' but your resume shows no evidence of it."
                f" Only add it if you genuinely have this experience."
                for s in missing[:6]
            ],
            "summary": (
                f"Emphasize your {', '.join(matched[:3])} experience"
                if matched
                else "Focus your summary on the responsibilities listed in the job."
            ),
        }

    @staticmethod
    def _match_explanation(ctx: dict) -> dict:
        overall = ctx.get("overall", 0)
        strong = ctx.get("strong_matches", [])
        missing = ctx.get("missing_skills", [])
        text = f"This job matched {round(float(overall))}% overall."
        if strong:
            text += f" Strongest overlap: {', '.join(strong[:5])}."
        if missing:
            text += (
                f" The score is held back mainly by missing required skills:"
                f" {', '.join(missing[:5])}."
            )
        return {"explanation": text}

    @staticmethod
    def _interview_questions(ctx: dict) -> dict:
        role = ctx.get("target_role", "the role")
        difficulty = ctx.get("difficulty", "medium")
        count = int(ctx.get("question_count", 6))
        skills: list[str] = ctx.get("skills", [])
        projects: list[str] = ctx.get("projects", [])
        job_skills: list[str] = ctx.get("job_required_skills", [])
        questions: list[dict] = []

        for skill in skills[:max(2, count // 2)]:
            questions.append({
                "question": f"Your resume mentions {skill}. Walk me through how you"
                            f" used {skill} in a real project and one trade-off you faced.",
                "category": "resume",
                "difficulty": difficulty,
                "grounding": f"Resume lists the skill '{skill}'.",
            })
        for project in projects[:2]:
            questions.append({
                "question": f"Tell me about '{project}'. What was the hardest"
                            " technical decision and how did you validate it?",
                "category": "project",
                "difficulty": difficulty,
                "grounding": f"Resume describes the project '{project}'.",
            })
        for skill in job_skills[:2]:
            questions.append({
                "question": f"The {role} role requires {skill}. How would you"
                            f" approach a task using {skill}, given your background?",
                "category": "technical",
                "difficulty": difficulty,
                "grounding": f"Target job requires '{skill}'.",
            })
        questions.append({
            "question": "Describe a time you received difficult feedback on your"
                        " work. What did you change afterwards?",
            "category": "behavioral",
            "difficulty": "easy",
            "grounding": "Standard behavioral coverage.",
        })
        questions.append({
            "question": f"Sketch the high-level design of a system relevant to a"
                        f" {role}: what components, data stores and failure modes"
                        " would you consider?",
            "category": "system_design",
            "difficulty": "hard" if difficulty == "hard" else "medium",
            "grounding": f"Target role '{role}'.",
        })
        fillers = [
            {"question": f"What attracts you to working as a {role}, and what"
                         " kind of problems do you want to own?",
             "category": "hr", "difficulty": "easy",
             "grounding": "Standard coverage - no user-specific context available."},
            {"question": "You discover a production incident an hour before a"
                         " release deadline. Walk me through what you do first"
                         " and why.",
             "category": "situational", "difficulty": difficulty,
             "grounding": "Standard coverage - no user-specific context available."},
            {"question": f"How do you keep your {role} skills current? Give a"
                         " recent example of something you learned and applied.",
             "category": "behavioral", "difficulty": "easy",
             "grounding": "Standard coverage - no user-specific context available."},
        ]
        for filler in fillers:
            if len(questions) >= count:
                break
            questions.append(filler)
        return {"questions": questions[:count]}

    @staticmethod
    def _interview_feedback(ctx: dict) -> dict:
        answer: str = ctx.get("answer", "")
        question: str = ctx.get("question", "")
        words = answer.split()
        lowered = answer.lower()

        completeness = min(100.0, len(words) / 1.2)
        q_terms = {w.strip("?,.").lower() for w in question.split() if len(w) > 4}
        overlap = sum(1 for t in q_terms if t in lowered)
        relevance = min(100.0, 30 + overlap * 12) if words else 0.0
        structure = min(100.0, 40 + 15 * sum(1 for m in _STRUCTURE_MARKERS if m in lowered))
        clarity = max(20.0, min(95.0, 100 - abs(len(words) - 120) * 0.3)) if words else 0.0
        technical = min(100.0, 40 + overlap * 10) if words else 0.0
        score = round(
            0.3 * relevance + 0.2 * technical + 0.2 * completeness
            + 0.15 * clarity + 0.15 * structure, 1
        )

        strengths, weaknesses, tips = [], [], []
        if overlap >= 3:
            strengths.append("Directly addresses key terms from the question.")
        if structure > 70:
            strengths.append("Answer has a clear narrative structure.")
        if len(words) < 40:
            weaknesses.append("Answer is short; add concrete details and an example.")
            tips.append("Aim for 90-150 words with one specific example.")
        if overlap < 2:
            weaknesses.append("Answer drifts from what was asked.")
            tips.append("Restate the question in your first sentence to stay anchored.")
        if not any(ch.isdigit() for ch in answer):
            tips.append("If you have real numbers (scale, latency, impact), include one.")
        if not strengths:
            strengths.append("You attempted a direct answer.")

        return {
            "score": score,
            "relevance": round(relevance, 1),
            "technical_correctness": round(technical, 1),
            "clarity": round(clarity, 1),
            "completeness": round(completeness, 1),
            "structure": round(structure, 1),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggested_structure": (
                "Situation -> Task -> Action -> Result. Lead with context in one"
                " sentence, describe your specific actions, close with the outcome."
            ),
            "improvement_tips": tips or ["Add one concrete, verifiable example."],
        }

    @staticmethod
    def _learning_roadmap(ctx: dict) -> dict:
        skill = ctx.get("skill", "the skill")
        priority = ctx.get("priority", "important")
        return {
            "skill": skill,
            "priority": priority,
            "prerequisites": ctx.get("known_related_skills", [])[:3],
            "stages": [
                {"period": "Week 1", "focus": f"Fundamentals of {skill}: core concepts and setup.",
                 "practice_task": f"Complete a guided beginner exercise using {skill}."},
                {"period": "Week 2", "focus": f"Core workflows in {skill} used in production teams.",
                 "practice_task": f"Rebuild a small existing feature with {skill}."},
                {"period": "Week 3", "focus": f"Integration: combine {skill} with your current stack.",
                 "practice_task": f"Add {skill} to one of your existing projects."},
                {"period": "Week 4", "focus": "Ship and document a small end-to-end project.",
                 "practice_task": "Deploy the project and write a README explaining decisions."},
            ],
            "project_idea": f"A small portfolio project where {skill} solves a real"
                            " problem you already understand from your own work.",
            "estimated_weeks": 4,
        }
