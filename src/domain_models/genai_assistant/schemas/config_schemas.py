# GenAI_Factory/src/domain_models/genai_assistant/schemas/config_schemas.py

from pydantic import BaseModel, Field, PositiveInt
from typing import List, Optional

# --- 1. LLM Configuration Schema (Mới) ---
class LLMConfigSchema(BaseModel):
    """Schema for validating LLM connection and resilience configuration."""
    model_name: str = Field(..., description="The primary LLM model name (e.g., gpt-4o, claude-3).")
    endpoint: str = Field(..., description="The API endpoint or internal service route.")
    retry_attempts: PositiveInt = Field(3, description="Number of times to retry on API failure (Hardening).")
    fallback_model: Optional[str] = Field(
        None, 
        description="A lower-cost or more stable model to use if the primary fails."
    )
    timeout_seconds: PositiveInt = Field(30, description="Max request time to prevent hanging.")


# --- 2. Assistant Core Configuration Schema ---
class AssistantConfigSchema(BaseModel):
    """Schema for validating assistant_config.yaml."""
    persona: str = Field(..., description="The defined role and personality of the assistant.")
    max_history_tokens: PositiveInt = Field(
        2000, 
        description="The maximum number of tokens allowed for conversation memory (Cost Control)."
    )
    default_pipeline: str = Field("conversation", description="The default pipeline for basic queries.")
    welcome_message: str = Field(..., description="The first message sent to a new user.")


# --- 3. Safety Configuration Schema ---
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
    output_toxicity_action: str = Field(
        "REDACT", 
        description="Action on toxic output: 'REDACT' (return safe message) or 'BLOCK' (raise error)."
    )
    pii_patterns: List[str] = Field(
        [], 
        description="List of regex patterns for PII redaction (Critical Hardening)."
    )