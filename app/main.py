from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .database import Base, engine, get_db
from .evaluator import evaluate_answer
from .models import Answer, Evaluation, Question, User


BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="AI Communication Coach", version="2.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

DEFAULT_QUESTIONS = [
    "Tell me about a difficult problem you solved at work.",
    "Explain a decision you made when the data was incomplete.",
    "Describe a process you improved and the measurable result.",
    "How would you explain a technical issue to a senior business stakeholder?",
    "What professional skill are you currently developing, and why?",
]


def build_weakness_profile(history):
    evaluated = [a.evaluation for a in history if a.evaluation]
    if len(evaluated) < 5:
        return None
    dimensions = {
        "Clarity": sum(e.clarity for e in evaluated) / len(evaluated),
        "Structure": sum(e.structure for e in evaluated) / len(evaluated),
        "Directness": sum(e.directness for e in evaluated) / len(evaluated),
        "Reasoning": sum(e.reasoning for e in evaluated) / len(evaluated),
    }
    counts, rules = {}, {}
    for e in evaluated:
        counts[e.main_weakness] = counts.get(e.main_weakness, 0) + 1
        rules[e.main_weakness] = e.training_rule
    patterns = sorted(counts, key=counts.get, reverse=True)[:3]
    return {
        "averages": {k: round(v, 1) for k, v in dimensions.items()},
        "weakest_dimension": min(dimensions, key=dimensions.get),
        "patterns": [{"name": p, "count": counts[p], "advice": rules[p]} for p in patterns],
        "next_drill": evaluated[0].follow_up_exercise,
    }


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        if not db.scalar(select(Question.id).limit(1)):
            db.add_all([Question(text=q) for q in DEFAULT_QUESTIONS])
            db.commit()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request, user_id: int | None = None, db: Session = Depends(get_db)):
    user = db.get(User, user_id) if user_id else None
    question = db.scalar(select(Question).order_by(Question.id))
    history = []
    if user:
        history = db.scalars(
            select(Answer).options(joinedload(Answer.question), joinedload(Answer.evaluation))
            .where(Answer.user_id == user.id).order_by(Answer.created_at.desc()).limit(10)
        ).all()
    return templates.TemplateResponse("index.html", {
        "request": request, "user": user, "question": question, "history": history,
        "weaknesses_unlocked": len(history) >= 5,
        "weakness_profile": build_weakness_profile(history),
    })


@app.post("/users")
def create_user(name: str = Form(...), db: Session = Depends(get_db)):
    cleaned = name.strip()
    if not cleaned:
        raise HTTPException(400, "Name is required")
    user = db.scalar(select(User).where(User.name == cleaned))
    if not user:
        user = User(name=cleaned)
        db.add(user)
        db.commit()
        db.refresh(user)
    return RedirectResponse(f"/?user_id={user.id}", status_code=303)


@app.post("/answers")
def submit_answer(
    user_id: int = Form(...), question_id: int = Form(...), text: str = Form(...),
    thinking_time_seconds: int = Form(0), writing_time_seconds: int = Form(0),
    db: Session = Depends(get_db),
):
    user, question = db.get(User, user_id), db.get(Question, question_id)
    cleaned = text.strip()
    if not user or not question or not cleaned:
        raise HTTPException(400, "Valid user, question and answer are required")
    answer = Answer(
        user_id=user.id, question_id=question.id, text=cleaned,
        thinking_time_seconds=max(0, thinking_time_seconds),
        writing_time_seconds=max(0, writing_time_seconds),
        word_count=len(cleaned.split()),
    )
    db.add(answer)
    db.flush()
    result, evaluator = evaluate_answer(question.text, cleaned)
    db.add(Evaluation(answer_id=answer.id, evaluator=evaluator, **result.model_dump()))
    db.commit()
    return RedirectResponse(f"/?user_id={user.id}", status_code=303)


@app.get("/api/users/{user_id}/history")
def user_history(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    answers = db.scalars(
        select(Answer).options(joinedload(Answer.question), joinedload(Answer.evaluation))
        .where(Answer.user_id == user_id).order_by(Answer.created_at.desc())
    ).all()
    return {
        "user": {"id": user.id, "name": user.name},
        "answers": [{
            "id": a.id, "question": a.question.text, "answer": a.text,
            "word_count": a.word_count, "thinking_time_seconds": a.thinking_time_seconds,
            "writing_time_seconds": a.writing_time_seconds,
            "evaluation": ({k: getattr(a.evaluation, k) for k in (
                "clarity", "structure", "directness", "reasoning", "main_strength",
                "main_weakness", "evidence", "training_rule", "follow_up_exercise", "evaluator"
            )} if a.evaluation else None),
        } for a in answers],
    }
