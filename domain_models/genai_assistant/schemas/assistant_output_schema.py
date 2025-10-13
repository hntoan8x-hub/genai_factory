from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class AssistantOutputSchema(BaseModel):
    """
    Schema for the standardized output of the Assistant's main API.

    Ensures that responses consistently contain a message and optional metadata.
    """
    response: str = Field(..., description="The generated response from the assistant.")
    pipeline: str = Field(..., description="The pipeline that was used to generate the response.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata, such as sources or evaluation scores.")
