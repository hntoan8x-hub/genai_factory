# GenAI_Factory/src/domain_models/genai_assistant/schemas/eval_schema.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# --- 1. Base Evaluation Result ---
class EvaluationResult(BaseModel):
    """
    Schema for the result of a single, standardized evaluation metric.
    """
    evaluator: str = Field(..., description="The name of the evaluator that was run.")
    metric_name: str = Field(..., description="The name of the metric, e.g., 'BLEU', 'coherence_score'.")
    score: float = Field(..., description="A quantitative score (0.0-1.0).")
    is_pass: bool = Field(True, description="Indicates if the result meets the defined quality threshold.")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details about the evaluation.")
    reasoning_llm: Optional[str] = Field(None, description="Reasoning from LLM-as-a-Judge, if applicable.")


# --- 2. Safety-Specific Evaluation (CRITICAL) ---
class SafetyEvaluation(BaseModel):
    """
    Schema for a safety-related evaluation, ensuring critical flags are tracked.
    """
    toxicity_score: float = Field(..., description="The toxicity score (0-1).")
    bias_score: float = Field(..., description="The bias score (0-1).")
    pii_redacted_count: int = Field(0, description="Count of PII instances redacted.")
    is_safe: bool = Field(..., description="A boolean indicating if the output is considered safe.")
    
    # Jailbreak/Injection Hardening
    jailbreak_detected: bool = Field(
        False, 
        description="Flag for input: potential attempt to bypass system instructions."
    )
    prompt_injection_score: float = Field(
        0.0, 
        description="Score indicating likelihood of input being a prompt injection."
    )