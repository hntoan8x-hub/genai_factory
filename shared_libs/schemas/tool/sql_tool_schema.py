from pydantic import BaseModel, Field
from typing import List, Dict, Any

# File: shared_libs/schemas/tool_schema.py

class SQLToolInput(BaseModel):
    """Schema for validating input to the SQL Tool."""
    
    # Enforce that the input is explicitly named 'sql_query'
    sql_query: str = Field(
        ..., 
        description="The SELECT query to execute against the database. MUST be a read-only query."
    )
    
class SQLToolOutput(BaseModel):
    """Schema for validating and structuring output from the SQL Tool."""
    
    # Output is structured as a list of dictionary rows
    query_result: List[Dict[str, Any]] = Field(
        ...,
        description="The list of rows returned from the database query."
    )
    # Metadata for transparency/debugging
    rows_returned: int = Field(
        ...,
        description="The number of rows returned."
    )