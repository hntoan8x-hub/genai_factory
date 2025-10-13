from pydantic import BaseModel, Field
from typing import Dict, Any

class ToolInputSchema(BaseModel):
    """
    Base schema for all tool inputs.
    
    Specific tools can inherit from this to add their own fields.
    """
    input_data: Dict[str, Any] = Field(..., description="The input data for the tool.")

class ToolOutputSchema(BaseModel):
    """
    Base schema for all tool outputs.
    
    Specific tools can inherit from this to add their own fields.
    """
    output_data: Any = Field(..., description="The output data from the tool.")
    success: bool = Field(True, description="Indicates if the tool execution was successful.")
    error: str = Field(None, description="An error message if the execution failed.")
