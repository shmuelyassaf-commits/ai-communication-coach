# AI Communication Coach — V2

A working FastAPI application for timed English communication practice. Every answer receives a structured evaluation, is saved with its metrics, and produces one targeted follow-up exercise.

## V2 capabilities

- Create or reuse a user by name
- Timed thinking and writing practice
- PostgreSQL persistence with a SQLite local fallback
- Structured scores: clarity, structure, directness, and reasoning
- Specific strength, weakness, evidence, and training rule
- One targeted follow-up exercise per answer
- OpenAI structured-output evaluation when `OPENAI_API_KEY` is configured
- Deterministic local evaluator when no key is configured or the API is unavailable
- User history API at `/api/users/{user_id}/history`
- Personal weakness area unlocked after five answers

## Run with Docker

```bash
cp .env.example .env
# Optional: add OPENAI_API_KEY to .env
docker compose up --build
```

Open <http://localhost:8000>.

## Run locally without PostgreSQL or an AI key

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The local run creates `communication_coach.db`. The app remains fully usable through the rule-based evaluator.

## Data model

`users → answers → evaluations`, with each answer linked to one seeded practice question. Evaluation data is stored in individual columns so future weakness aggregation is straightforward.

## Test

```bash
pytest -q
```

## Next milestone

Aggregate the last five evaluations into a weakness profile, then select the next question dynamically from that profile. Multi-agent orchestration should wait until the single evaluator is stable and measurable.
