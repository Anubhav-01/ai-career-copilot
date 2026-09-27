"""Interview preparation and mock interviews.

Question generation is RAG-grounded: the target role is used as a semantic
query over the user's indexed resume chunks, and the retrieved evidence
(plus extracted skills/projects and the target job's requirements) forms
the generation context. Every question stores its grounding.
"""
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.embeddings.factory import get_embedding_provider
from app.ai.guardrails import call_structured
from app.ai.llm.factory import get_llm_provider
from app.ai.prompts import SYSTEMS, build_prompt
from app.ai.rag.context import build_context
from app.ai.rag.retriever import Retriever
from app.core.cache import get_cache
from app.core.errors import NotFoundError, ValidationFailedError
from app.models.interview import Interview, InterviewAnswer, InterviewQuestion
from app.models.user import User
from app.repositories.audit import AuditRepository
from app.repositories.interview import InterviewRepository
from app.repositories.job import JobRepository
from app.repositories.resume import ResumeRepository
from app.schemas.interview import (
    QUESTION_CATEGORIES,
    GeneratedQuestionList,
    InterviewCreateRequest,
    InterviewFeedback,
    InterviewReport,
)


class InterviewService:
    def __init__(self, db: Session):
        self.db = db
        self.interviews = InterviewRepository(db)
        self.resumes = ResumeRepository(db)
        self.jobs = JobRepository(db)
        self.audit = AuditRepository(db)

    # --- creation ---------------------------------------------------------

    def create(self, user: User, payload: InterviewCreateRequest) -> Interview:
        resume = None
        if payload.resume_id:
            resume = self.resumes.get_for_user(payload.resume_id, user.id)
            if resume is None:
                raise NotFoundError("Resume not found.")
        job = None
        if payload.job_id:
            job = self.jobs.get_for_user(payload.job_id, user.id)
            if job is None:
                raise NotFoundError("Job not found.")

        context = self._build_generation_context(user, payload, resume, job)
        prompt = build_prompt(
            instruction=(
                f"Generate {payload.question_count} interview questions for a"
                f" '{payload.target_role}' candidate. Ground questions in the"
                " candidate's actual resume evidence and the job requirements"
                " whenever available; avoid generic questions when specific"
                " context exists. Cover a mix of categories"
                f" ({', '.join(payload.categories or QUESTION_CATEGORIES)})."
                " For each question include 'grounding': the evidence that"
                " motivated it."
            ),
            context=context,
            schema_hint=("{questions: [{question, category, difficulty,"
                         " grounding}]}"),
        )
        generated = call_structured(
            get_llm_provider(), "interview_questions",
            SYSTEMS["interview_questions"], prompt, GeneratedQuestionList,
            max_tokens=2000,
        )
        if not generated.questions:
            raise ValidationFailedError("Could not generate questions. Try again.")

        allowed = set(payload.categories or QUESTION_CATEGORIES)
        questions = [
            q for q in generated.questions
            if q.category in allowed or q.category in QUESTION_CATEGORIES
        ][: payload.question_count]

        interview = self.interviews.add(Interview(
            user_id=user.id,
            resume_id=resume.id if resume else None,
            job_id=job.id if job else None,
            target_role=payload.target_role,
            difficulty=payload.difficulty,
            mode=payload.mode,
            status="created",
        ))
        self.interviews.add_questions([
            InterviewQuestion(
                interview_id=interview.id, order_index=index,
                category=q.category if q.category in QUESTION_CATEGORIES else "technical",
                difficulty=q.difficulty if q.difficulty in ("easy", "medium", "hard")
                else payload.difficulty,
                question=q.question, grounding=q.grounding or None,
            )
            for index, q in enumerate(questions)
        ])
        self.audit.log("interview.create", user_id=user.id,
                       resource_type="interview", resource_id=str(interview.id))
        return interview

    def _build_generation_context(self, user, payload, resume, job) -> dict:
        skills: list[str] = []
        projects: list[str] = []
        resume_evidence = ""
        if resume is not None and resume.status == "completed":
            skills = [s.normalized for s in resume.skills][:12]
            projects = [
                p.get("name", "") for p in (resume.parsed or {}).get("projects", [])
                if p.get("name")
            ][:4]
            retriever = Retriever(self.db, get_embedding_provider())
            chunks = retriever.search(
                user.id,
                query=f"experience relevant to {payload.target_role}",
                top_k=6, document_type="resume", document_id=resume.id,
            )
            resume_evidence = build_context(chunks, word_budget=600)

        job_required: list[str] = []
        if job is not None and job.analysis:
            job_required = job.analysis.get("required_skills", [])[:10]

        return {
            "target_role": payload.target_role,
            "difficulty": payload.difficulty,
            "question_count": payload.question_count,
            "skills": skills,
            "projects": projects,
            "resume_evidence": resume_evidence,
            "job_required_skills": job_required,
            "job_title": job.title if job else "",
        }

    # --- answering (mock interview loop) -----------------------------------

    def answer(self, user: User, interview_id: uuid.UUID,
               question_id: uuid.UUID, answer_text: str) -> tuple[
                   InterviewFeedback, InterviewQuestion | None, bool]:
        interview = self.get_owned(user, interview_id)
        question = self.interviews.get_question(question_id)
        if question is None or question.interview_id != interview.id:
            raise NotFoundError("Question not found in this interview.")
        if question.answer is not None:
            raise ValidationFailedError("This question was already answered.")

        prompt = build_prompt(
            instruction=(
                "Evaluate this interview answer. Score each dimension 0-100"
                " and give concrete strengths, weaknesses, a suggested answer"
                " structure and improvement tips. Judge only the answer text."
            ),
            context={
                "question": question.question,
                "category": question.category,
                "difficulty": question.difficulty,
                "target_role": interview.target_role,
                "answer": answer_text,
            },
            schema_hint=("{score, relevance, technical_correctness, clarity,"
                         " completeness, structure, strengths[], weaknesses[],"
                         " suggested_structure, improvement_tips[]}"),
        )
        feedback = call_structured(
            get_llm_provider(), "interview_feedback",
            SYSTEMS["interview_feedback"], prompt, InterviewFeedback,
            max_tokens=900,
        )

        self.interviews.add_answer(InterviewAnswer(
            question=question,  # relationship (not raw FK) keeps the
            answer_text=answer_text,  # in-session backref consistent
            score=feedback.score,
            feedback=feedback.model_dump(),
        ))
        if interview.status == "created":
            interview.status = "in_progress"

        next_question = self._next_unanswered(interview)
        completed = next_question is None
        if completed:
            interview.status = "completed"
            interview.completed_at = datetime.now(timezone.utc)
            interview.report = self._build_report(interview).model_dump()
            get_cache().delete_prefix(f"dashboard:{user.id}")
        self.db.flush()
        return feedback, next_question, completed

    def _next_unanswered(self, interview: Interview) -> InterviewQuestion | None:
        for question in interview.questions:
            if question.answer is None:
                return question
        return None

    # --- report ---------------------------------------------------------------

    def report(self, user: User, interview_id: uuid.UUID) -> InterviewReport:
        interview = self.get_owned(user, interview_id)
        if interview.report:
            return InterviewReport.model_validate(interview.report)
        return self._build_report(interview)

    def _build_report(self, interview: Interview) -> InterviewReport:
        answers = self.interviews.answers_for_interview(interview.id)
        if not answers:
            return InterviewReport(total_questions=len(interview.questions))

        by_category: dict[str, list[float]] = defaultdict(list)
        strengths: list[str] = []
        weaknesses: list[str] = []
        tips: list[str] = []
        for answer in answers:
            question = answer.question
            if answer.score is not None:
                by_category[question.category].append(answer.score)
            feedback = answer.feedback or {}
            strengths.extend(feedback.get("strengths", [])[:1])
            weaknesses.extend(feedback.get("weaknesses", [])[:1])
            tips.extend(feedback.get("improvement_tips", [])[:1])

        scores = [a.score for a in answers if a.score is not None]
        return InterviewReport(
            overall_score=round(sum(scores) / len(scores), 1) if scores else 0,
            answered=len(answers),
            total_questions=len(interview.questions),
            category_scores={
                cat: round(sum(vals) / len(vals), 1)
                for cat, vals in by_category.items()
            },
            strengths=list(dict.fromkeys(strengths))[:5],
            weaknesses=list(dict.fromkeys(weaknesses))[:5],
            improvement_tips=list(dict.fromkeys(tips))[:5],
        )

    def get_owned(self, user: User, interview_id: uuid.UUID) -> Interview:
        interview = self.interviews.get_for_user(interview_id, user.id)
        if interview is None:
            raise NotFoundError("Interview not found.")
        return interview
