from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    language: Mapped[str] = mapped_column(String(20), default="English")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    answers: Mapped[list["Answer"]] = relationship(back_populates="user")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(50), default="professional")
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    answers: Mapped[list["Answer"]] = relationship(back_populates="question")


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    text: Mapped[str] = mapped_column(Text)
    thinking_time_seconds: Mapped[int] = mapped_column(Integer, default=0)
    writing_time_seconds: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[User] = relationship(back_populates="answers")
    question: Mapped[Question] = relationship(back_populates="answers")
    evaluation: Mapped["Evaluation | None"] = relationship(back_populates="answer", uselist=False)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    answer_id: Mapped[int] = mapped_column(ForeignKey("answers.id"), unique=True, index=True)
    clarity: Mapped[float] = mapped_column(Float)
    structure: Mapped[float] = mapped_column(Float)
    directness: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[float] = mapped_column(Float)
    main_strength: Mapped[str] = mapped_column(Text)
    main_weakness: Mapped[str] = mapped_column(Text)
    evidence: Mapped[str] = mapped_column(Text)
    training_rule: Mapped[str] = mapped_column(Text)
    follow_up_exercise: Mapped[str] = mapped_column(Text)
    evaluator: Mapped[str] = mapped_column(String(40), default="local")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    answer: Mapped[Answer] = relationship(back_populates="evaluation")
