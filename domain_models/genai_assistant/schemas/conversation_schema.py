from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ConversationTurn(BaseModel):
    """
    Schema for a single turn in a conversation.
    """
    role: str = Field(..., description="The role of the speaker, e.g., 'user' or 'assistant'.")
    content: str = Field(..., description="The content of the message.")
    timestamp: float = Field(..., description="The timestamp of the message.")

class ConversationHistory(BaseModel):
    """
    Schema for tracking a full conversation history.
    """
    session_id: str = Field(..., description="A unique identifier for the conversation session.")
    history: List[ConversationTurn] = Field([], description="A list of all conversation turns.")
    summary: str = Field(None, description="A summary of the conversation for long-term memory.")
