from typing import Dict, List

from pydantic import BaseModel, ConfigDict


class AnalysisResponse(BaseModel):
    tag_accuracy: Dict[str, float]
    rating_accuracy: Dict[str, float]
    average_solve_time: float
    insights: List[str]

    model_config = ConfigDict(from_attributes=True)
