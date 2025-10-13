# domain_models/genai_assistant/schemas/config_schemas.py

from pydantic import BaseModel, Field, PositiveInt
from typing import List, Optional

# --- 1. Assistant Core Configuration Schema ---
class AssistantConfigSchema(BaseModel):
    """Schema for validating assistant_config.yaml."""
    persona: str = Field(..., description="The defined role and personality of the assistant.")
    max_history_tokens: PositiveInt = Field(
        2000, 
        description="The maximum number of tokens allowed for conversation memory."
    )
    default_pipeline: str = Field(..., description="The name of the pipeline used for basic queries.")
    welcome_message: str = Field(..., description="The first message sent to a new user.")

# --- 2. Safety Configuration Schema ---
class SafetyConfigSchema(BaseModel):
    """Schema for validating safety_config.yaml."""
    moderation_api_enabled: bool = True
    toxicity_threshold: float = Field(
        0.8, 
        ge=0.0, 
        le=1.0, 
        description="Threshold score (0.0-1.0) above which output is flagged."
    )
    input_injection_check: bool = Field(True, description="Enables check for prompt injection patterns.")
    blocklist: List[str] = Field([], description="List of banned words or phrases.")

# --- 3. Retriever Configuration Schema ---
class RetrieverConfigSchema(BaseModel):
    """Schema for validating retriever_config.yaml."""
    top_k_retrieval: PositiveInt = Field(
        5, 
        description="Number of top documents to retrieve from the vector database."
    )
    reranker_enabled: bool = False
    reranker_model_name: Optional[str] = None
    vector_db_endpoint: str = Field(..., description="The connection endpoint for the vector database.")