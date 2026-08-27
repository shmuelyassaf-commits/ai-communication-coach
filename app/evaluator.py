import os
import re

from .schemas import EvaluationResult


SYSTEM_PROMPT = """You are a concise English business-communication coach.
Evaluate only the submitted answer against the question. Return fair, specific,
actionable feedback. Scores are 0-10. Evidence must point to wording or structure
in the answer. The follow-up exercise must take 2-4 minutes and directly train the
main weakness. Do not invent facts about the writer."""


def _local_evaluation(question: str, answer: str) -> EvaluationResult:
    words = re.findall(r"\b[\w'-]+\b", answer)
    sentences = [s.strip() for s in re.split(r"[.!?]+", answer) if s.strip()]
    connectors = sum(answer.lower().count(x) for x in ("because", "therefore", "for example", "however"))
    has_early_point = bool(sentences and len(sentences[0].split()) <= 22)
    clarity = min(9.0, 4.5 + min(len(sentences), 4) * 0.7)
    structure = min(9.0, 4.5 + min(connectors, 3) * 0.8 + (0.8 if len(sentences) >= 3 else 0))
    directness = 7.5 if has_early_point else 5.5
    reasoning = min(9.0, 4.5 + min(connectors, 3) * 0.9 + (0.7 if len(words) >= 45 else 0))

    if len(words) < 25:
        weakness = "The answer is too brief to fully support its main point"
        rule = "Add one reason and one concrete example"
        exercise = f"Answer again in exactly 4 sentences: position, reason, example, conclusion. Question: {question}"
    elif not has_early_point:
        weakness = "The main point appears too late"
        rule = "State your position in the first sentence"
        exercise = f"Rewrite only the opening in 20 words or fewer, stating your position immediately. Question: {question}"
    elif connectors == 0:
        weakness = "The reasoning links are not explicit"
        rule = "Connect the claim to evidence with because or for example"
        exercise = "Rewrite two sentences using this pattern: I believe X because Y. For example, Z."
    else:
        weakness = "The conclusion could be more decisive"
        rule = "End with one clear takeaway or action"
        exercise = "Write a one-sentence conclusion of no more than 18 words that states the takeaway or next action."

    strength = "The response communicates a recognizable main idea" if words else "The response was submitted"
    evidence = sentences[0][:180] if sentences else "No substantive sentence was provided"
    return EvaluationResult(
        clarity=round(clarity, 1), structure=round(structure, 1),
        directness=round(directness, 1), reasoning=round(reasoning, 1),
        main_strength=strength, main_weakness=weakness, evidence=evidence,
        training_rule=rule, follow_up_exercise=exercise,
    )


def evaluate_answer(question: str, answer: str) -> tuple[EvaluationResult, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _local_evaluation(question, answer), "local"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.parse(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question:\n{question}\n\nAnswer:\n{answer}"},
            ],
            text_format=EvaluationResult,
        )
        if response.output_parsed:
            return response.output_parsed, "openai"
    except Exception:
        pass
    return _local_evaluation(question, answer), "local-fallback"
