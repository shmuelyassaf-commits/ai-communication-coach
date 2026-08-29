from app.evaluator import evaluate_answer
from app.main import build_weakness_profile, select_next_question
from types import SimpleNamespace


def test_local_evaluator_returns_structured_result(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result, source = evaluate_answer(
        "Describe a process you improved.",
        "I improved our reporting process because it was slow. For example, I automated validation and reduced the work from hours to minutes. The team could then focus on analysis. My recommendation is to automate the recurring controls first.",
    )
    assert source == "local"
    assert 0 <= result.clarity <= 10
    assert result.follow_up_exercise
    assert result.training_rule


def test_next_question_targets_weakest_dimension_after_five_answers():
    questions = [SimpleNamespace(text=text) for text in (
        "Tell me about a difficult problem you solved at work.",
        "Explain a decision you made when the data was incomplete.",
        "Describe a process you improved and the measurable result.",
        "How would you explain a technical issue to a senior business stakeholder?",
        "What professional skill are you currently developing, and why?",
    )]
    evaluations = [SimpleNamespace(
        clarity=score, structure=8.0, directness=7.0, reasoning=7.5,
        main_weakness="Make the explanation easier to follow",
        training_rule="Use shorter sentences", follow_up_exercise="Explain it again",
    ) for score in (4.0, 4.5, 5.0, 5.5, 6.0)]
    history = [SimpleNamespace(evaluation=item) for item in evaluations]

    profile = build_weakness_profile(history)
    selected = select_next_question(questions, history, profile)

    assert profile["weakest_dimension"] == "Clarity"
    assert selected.text == "How would you explain a technical issue to a senior business stakeholder?"


def test_next_question_rotates_before_profile_is_unlocked():
    questions = [SimpleNamespace(text=f"Question {number}") for number in range(3)]
    history = [SimpleNamespace(evaluation=None) for _ in range(4)]

    assert select_next_question(questions, history, None).text == "Question 1"
