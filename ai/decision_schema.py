from pydantic import BaseModel, Field


class Decision(BaseModel):
    selected_candidate_index: int = Field(..., ge=1, description="The 1-based index of the selected candidate.")
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)