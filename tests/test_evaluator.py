from app.evaluator import evaluate_answer


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
