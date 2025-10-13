# shared_libs/configs/schemas.py

from pydantic import BaseModel, Field, SecretStr, PositiveInt, root_validator
from typing import Dict, Any, List, Optional
from pathlib import Path

# --- 1. LLM Schemas ---

class LLMBaseConfig(BaseModel):
    """Base schema for all LLM configurations."""
    type: str
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Sampling temperature.")
    max_tokens: Optional[PositiveInt] = Field(None, description="Max tokens to generate.")

class OpenAILLMConfig(LLMBaseConfig):
    api_key: SecretStr
    model_name: str
    
class AnthropicLLMConfig(LLMBaseConfig):
    api_key: SecretStr
    model_name: str

class HuggingFaceLLMConfig(LLMBaseConfig):
    model_path: Path # Validate path existence
    device: str = "auto"

# --- 2. Tool Schemas ---

class SQLToolSchema(BaseModel):
    type: str = "sql"
    db_connection_string: str = Field(..., description="Connection string for the database.")

class WebToolSchema(BaseModel):
    type: str = "web"
    api_key: SecretStr

# --- 3. Agent Schemas ---

class ReActAgentSchema(BaseModel):
    type: str = "react"
    llm_config_key: str = Field(..., description="Key to look up the LLM config in LLMConfig.")
    tools: List[str]
    max_loops: PositiveInt = 10
    verbose: bool = True

# --- 4. Orchestrator and Evaluator Schemas ---

class EvaluatorEntry(BaseModel):
    type: str
    enabled: bool
    # Allows for extra context like ground_truth_key for hallucination
    context: Dict[str, Any] = {} 

class EvaluatorConfigSchema(BaseModel):
    evaluators: List[EvaluatorEntry]