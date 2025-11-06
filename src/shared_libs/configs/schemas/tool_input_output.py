# shared_libs/configs/schemas/tool_input_output.py

from pydantic import BaseModel, Field, HttpUrl, PositiveInt
from typing import Dict, Any, List, Optional, Union
from shared_libs.configs.schemas import ToolName # Import Enums
from shared_libs.configs.schemas import ToolName # Giả định ToolName đã được định nghĩa trong __init__.py

# --- 1. BASE SCHEMAS ---
class ToolOutputBase(BaseModel):
    """Base schema cho mọi kết quả trả về của Tool."""
    status: str = Field('success', description="Trạng thái thực thi Tool.")
    result: Any = Field(..., description="Dữ liệu kết quả thô hoặc đã xử lý.")

class ToolInputBase(BaseModel):
    """Base schema cho mọi đầu vào của Tool (dùng để format lệnh gọi của Agent)."""
    tool_name: ToolName = Field(..., description="Tên Tool được gọi (Enum).")
    
# --- 2. INPUT SCHEMAS (Agent dùng để gọi Tool) ---

class SQLQueryInput(ToolInputBase):
    tool_name: ToolName = ToolName.SQL_EXECUTOR
    sql_query: str = Field(
        ..., 
        description="The SELECT query to execute against the database. MUST be a read-only query."
    )

class APIConnectorInput(ToolInputBase):
    tool_name: ToolName = ToolName.DATA_API_CONNECTOR
    endpoint_url: HttpUrl = Field(..., description="The full URL of the API endpoint to query.")
    params: Optional[Dict[str, Any]] = Field(None, description="Optional: Dictionary of query parameters.")

class AnalysisInput(ToolInputBase):
    tool_name: ToolName = ToolName.DATA_ANALYZER
    data: List[Dict] = Field(..., description="The raw list of data to analyze.")
    analysis_type: str = Field(..., description="The type of analysis to perform (e.g., 'calculate_mean').")
    target_column: str = Field(..., description="The column name to perform numerical analysis on.")
    
class VisualizerInput(ToolInputBase):
    tool_name: ToolName = ToolName.VISUALIZER
    data: List[Dict] = Field(..., description="The raw list of dictionaries/JSON data to visualize.")
    chart_type: str = Field(..., description="The type of chart required (e.g., 'bar', 'line', 'scatter').")
    x_axis: str = Field(..., description="The column name for the X-axis.")
    y_axis: Optional[str] = Field(None, description="The column name for the Y-axis.")

class SlackInput(ToolInputBase):
    tool_name: ToolName = ToolName.SLACK_NOTIFIER
    channel: str = Field(..., description="The Slack channel ID or name (e.g., #mlops-alerts).")
    message: str = Field(..., description="The text content of the notification to send.")

class FileReaderInput(ToolInputBase):
    tool_name: ToolName = ToolName.FILE_READER
    file_uri: str = Field(..., description="The URI (local path, S3, or GCS URL) of the file to read.")
    max_bytes: PositiveInt = Field(1048576, description="Maximum number of bytes to read (1MB limit for safety).")

class ParserInput(ToolInputBase):
    tool_name: ToolName = ToolName.JSON_XML_PARSER
    raw_data: str = Field(..., description="The raw JSON or XML string to parse.")
    data_type: str = Field(..., description="The type of data to parse ('json' or 'xml').")

class RetrievalInput(ToolInputBase):
    tool_name: ToolName = ToolName.DOCUMENT_RETRIEVER
    query: str = Field(..., description="The natural language query to search internal documents.")
    policy_type: Optional[str] = Field(None, description="Optional: Filter search to a specific policy type.")
    
# --- 3. OUTPUT SCHEMAS (Agent dùng để Validate kết quả) ---

class SQLQueryOutput(ToolOutputBase):
    query_result: List[Dict[str, Any]] = Field(..., description="The list of rows returned from the database query.")
    rows_returned: int = Field(..., description="The number of rows returned.")

class APIConnectorOutput(ToolOutputBase):
    status_code: int = Field(..., description="The HTTP status code.")
    data: Dict[str, Any] = Field(..., description="The JSON data returned from the API.")

class AnalysisOutput(ToolOutputBase):
    analysis_result: Dict[str, Any] = Field(..., description="The structured result of the statistical analysis.")
    summary: str = Field(..., description="A plain language summary of the findings.")
    
class VisualizerOutput(ToolOutputBase):
    python_code: str = Field(..., description="The generated Python code snippet for the visualization (e.g., Plotly code).")

class SlackOutput(ToolOutputBase):
    response_message: str = Field(..., description="The response message from the Slack API.")
    
class FileReaderOutput(ToolOutputBase):
    content: str = Field(..., description="The read content of the file (truncated if over limit).")
    size_bytes: int = Field(..., description="The size of the content read.")

class ParserOutput(ToolOutputBase):
    structured_data: Union[Dict, List, str] = Field(..., description="The parsed Python dictionary, list, or XML string representation.")

class RetrievedDocument(BaseModel):
    source_id: str
    snippet: str
    score: float
    
class RetrievalOutput(ToolOutputBase):
    retrieved_documents: List[RetrievedDocument] = Field(..., description="A list of relevant document snippets.")

# --- 4. REGISTRY MAP (Sử dụng bởi SchemaRegistry trong __init__.py) ---
TOOL_INPUT_MAP: Dict[ToolName, type[BaseModel]] = {
    ToolName.SQL_EXECUTOR: SQLQueryInput,
    ToolName.DATA_API_CONNECTOR: APIConnectorInput,
    ToolName.DATA_ANALYZER: AnalysisInput,
    ToolName.VISUALIZER: VisualizerInput,
    ToolName.SLACK_NOTIFIER: SlackInput,
    ToolName.FILE_READER: FileReaderInput,
    ToolName.JSON_XML_PARSER: ParserInput,
    ToolName.DOCUMENT_RETRIEVER: RetrievalInput,
    # Thêm các Tools còn lại (ví dụ: RISK_MODEL, CALCULATOR)
}