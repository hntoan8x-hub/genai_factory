from pydantic import BaseModel, Field
from typing import Optional

class AssistantInputSchema(BaseModel):
    """
    Schema for validating the input payload to the Assistant API.

    Enforces that all required fields are present and correctly typed.
    """
    user_id: str = Field(..., description="A unique identifier for the user.")
    query: str = Field(..., description="The user's text query.")
    pipeline_type: Optional[str] = Field("conversation_pipeline", description="The type of pipeline to use (e.g., 'conversation_pipeline', 'rag_pipeline').")
