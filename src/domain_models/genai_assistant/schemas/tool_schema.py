# GenAI_Factory/src/domain_models/genai_assistant/schemas/tool_schema.py

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class ToolInputSchema(BaseModel):
    """
    Base schema for all tool inputs (Data Validation Gate).
    """
    tool_name: str = Field(..., description="The name of the tool being called.")
    arguments: Dict[str, Any] = Field(..., description="The input arguments for the tool's execution.")


class ToolOutputSchema(BaseModel):
    """
    Base schema for all tool outputs (Error Handling Contract).
    """
    output_data: Any = Field(..., description="The output data from the tool's execution.")
    success: bool = Field(True, description="Indicates if the tool execution was successful.")
    error_message: Optional[str] = Field(None, description="An error message if the execution failed.")