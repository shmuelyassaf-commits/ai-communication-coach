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
    lower = answer.lower()
    connectors = sum(lower.count(x) for x in ("because", "therefore", "for example", "however", "so that", "as a result"))
    situation = any(x in lower for x in ("problem", "challenge", "process", "system", "task", "at work", "needed"))
    action = any(x in lower for x in ("i built", "i created", "i designed", "i mapped", "i analyzed", "i automated", "i led", "i changed", "i developed"))
    result = any(x in lower for x in ("result", "reduced", "improved", "increased", "saved", "faster", "accurate", "from days", "%", "hours", "minutes"))
    quantified = bool(re.search(r"\b\d+(?:\.\d+)?%?\b", answer)) or any(x in lower for x in ("days to hours", "hours to minutes"))
    has_early_point = bool(sentences and len(sentences[0].split()) <= 20 and any(x in lower[:120] for x in ("i ", "my ", "the problem", "the challenge")))
    avg_sentence = len(words) / max(1, len(sentences))
    clarity = 3.8 + min(len(words), 80) / 24 + (0.8 if 7 <= avg_sentence <= 22 else 0)
    if answer[:1].isupper() and answer.rstrip().endswith((".", "!", "?")):
        clarity += 0.5
    structure = 3.2 + 1.0 * situation + 1.4 * action + 1.4 * result + min(connectors, 2) * 0.5
    directness = 4.5 + (2.2 if has_early_point else 0) + (0.7 if action else 0) + (0.6 if result else 0)
    reasoning = 3.3 + min(connectors, 2) * 1.0 + 1.0 * action + 1.2 * result + 0.8 * quantified
    clarity, structure, directness, reasoning = [round(max(1.0, min(9.5, x)), 1) for x in (clarity, structure, directness, reasoning)]

    missing = []
    if not situation:
        missing.append("situation")
    if not action:
        missing.append("your specific action")
    if not result:
        missing.append("the result")

    if len(words) < 18:
        weakness = "The answer is too brief to fully support its main point"
        rule = "Add one reason and one concrete example"
        exercise = f"Answer again in exactly 4 sentences: position, reason, example, conclusion. Question: {question}"
    elif missing:
        weakness = "The answer is missing " + ", ".join(missing)
        rule = "Use STAR: Situation, Task, Action, Result — make your own action and the outcome explicit"
        exercise = f"Rewrite the answer in four labeled lines: Situation, Task, Action, Result. Add one measurable outcome. Question: {question}"
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

    if quantified and result:
        strength = "The answer includes a concrete, measurable result"
    elif action:
        strength = "Your personal action is visible in the answer"
    elif situation:
        strength = "The work context is recognizable"
    else:
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
