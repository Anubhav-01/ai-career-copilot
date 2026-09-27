import uuid

from sqlalchemy.orm import Session

from app.models.interview import Interview, InterviewAnswer, InterviewQuestion


class InterviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, interview: Interview) -> Interview:
        self.db.add(interview)
        self.db.flush()
        return interview

    def get_for_user(
        self, interview_id: uuid.UUID, user_id: uuid.UUID
    ) -> Interview | None:
        return (
            self.db.query(Interview)
            .filter(Interview.id == interview_id, Interview.user_id == user_id)
            .first()
        )

    def list_for_user(self, user_id: uuid.UUID) -> list[Interview]:
        return (
            self.db.query(Interview)
            .filter(Interview.user_id == user_id)
            .order_by(Interview.created_at.desc())
            .all()
        )

    def add_questions(self, questions: list[InterviewQuestion]) -> None:
        for question in questions:
            self.db.add(question)
        self.db.flush()

    def get_question(self, question_id: uuid.UUID) -> InterviewQuestion | None:
        return (
            self.db.query(InterviewQuestion)
            .filter(InterviewQuestion.id == question_id)
            .first()
        )

    def add_answer(self, answer: InterviewAnswer) -> InterviewAnswer:
        self.db.add(answer)
        self.db.flush()
        return answer

    def answers_for_interview(self, interview_id: uuid.UUID) -> list[InterviewAnswer]:
        return (
            self.db.query(InterviewAnswer)
            .join(InterviewQuestion, InterviewQuestion.id == InterviewAnswer.question_id)
            .filter(InterviewQuestion.interview_id == interview_id)
            .all()
        )

    def count(self) -> int:
        return self.db.query(Interview).count()
