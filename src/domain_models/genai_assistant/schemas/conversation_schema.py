# GenAI_Factory/src/domain_models/genai_assistant/schemas/conversation_schema.py

from pydantic import BaseModel, Field
from typing import List, Optional

class ConversationTurn(BaseModel):
    """Schema for a single turn in a conversation."""
    role: str = Field(..., description="The role of the speaker, e.g., 'user' or 'assistant'.")
    content: str = Field(..., description="The content of the message.")
    timestamp: float = Field(..., description="The timestamp of the message.")
    tokens: int = Field(0, description="Token count for this specific turn (for cost calculation).")


class ConversationHistory(BaseModel):
    """Schema for tracking a full conversation history (Memory Service Contract)."""
    session_id: str = Field(..., description="A unique identifier for the conversation session.")
    history: List[ConversationTurn] = Field([], description="A list of all conversation turns.")
    summary: Optional[str] = Field(None, description="A summary of the conversation for long-term memory.")
    total_tokens: int = Field(0, description="Total tokens in history + summary (CRITICAL for Token Control).")