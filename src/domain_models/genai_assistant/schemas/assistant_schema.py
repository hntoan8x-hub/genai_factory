# GenAI_Factory/src/domain_models/genai_assistant/schemas/assistant_schema.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# --- 1. Input Schema ---
class AssistantInputSchema(BaseModel):
    """Schema for validating the input payload to the Assistant API."""
    user_id: str = Field(..., description="A unique identifier for the user.")
    query: str = Field(..., description="The user's text query.")
    pipeline_type: Optional[str] = Field(
        "conversation", 
        description="The type of pipeline to use (e.g., 'conversation', 'rag', 'orchestration')."
    )
    # Thêm trường context để truyền các cờ runtime
    context: Optional[Dict[str, Any]] = Field(None, description="Additional runtime context/flags.")


# --- 2. Output Schema (CRITICAL HARDENING) ---
class AssistantOutputSchema(BaseModel):
    """
    Schema for the standardized output of the Assistant's main API.
    Includes cost and audit tracking information.
    """
    response: str = Field(..., description="The generated response from the assistant.")
    pipeline: str = Field(..., description="The pipeline that was used to generate the response.")
    request_id: str = Field(..., description="Unique ID for audit trail and tracing.")
    
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata, such as sources or evaluation scores.")
    
    # Audit & Cost Control Fields
    llm_cost_usd: float = Field(
        0.0, 
        description="Estimated cost of the LLM call in USD (Cost Governance)."
    )
    tokens_used: Dict[str, int] = Field(
        {"input": 0, "output": 0}, 
        description="Detailed token usage for input and output."
    )