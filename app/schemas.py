from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    clarity: float = Field(ge=0, le=10)
    structure: float = Field(ge=0, le=10)
    directness: float = Field(ge=0, le=10)
    reasoning: float = Field(ge=0, le=10)
    main_strength: str
    main_weakness: str
    evidence: str
    training_rule: str
    follow_up_exercise: str
