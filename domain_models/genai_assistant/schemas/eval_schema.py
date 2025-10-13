from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class EvaluationResult(BaseModel):
    """
    Schema for the result of a single evaluation.
    """
    evaluator: str = Field(..., description="The name of the evaluator that was run.")
    score: Optional[float] = Field(None, description="A quantitative score, if applicable.")
    metric_name: Optional[str] = Field(None, description="The name of the metric, e.g., 'BLEU', 'coherence_score'.")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details about the evaluation.")
    
class SafetyEvaluation(BaseModel):
    """
    Schema for a safety-related evaluation.
    """
    toxicity_score: float = Field(..., description="The toxicity score (0-1).")
    bias_score: float = Field(..., description="The bias score (0-1).")
    is_safe: bool = Field(..., description="A boolean indicating if the output is considered safe.")
