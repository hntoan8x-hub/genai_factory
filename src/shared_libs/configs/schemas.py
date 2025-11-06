# shared_libs/configs/schemas.py (Hoàn thiện)

from pydantic import BaseModel, Field, SecretStr, PositiveInt, EmailStr, HttpUrl
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from enum import Enum

# --- ENUMS (Đảm bảo kiểu dữ liệu đầu vào nhất quán) ---
class LLMType(str, Enum):
    OPENAI = 'openai'
    ANTHROPIC = 'anthropic'
    HUGGINGFACE = 'huggingface'

class ToolName(str, Enum):
    # Tools đã có
    SQL_EXECUTOR = 'sql_query_executor'
    WEB_SEARCH = 'web_tool'
    EMAIL_SENDER = 'email_tool'
    RISK_MODEL = 'risk_tool'
    CALCULATOR = 'calculator_tool' # Bổ sung tool calculator đã có
    
    # 🚨 CÁC TOOLS MỚI ĐƯỢC BỔ SUNG:
    DATA_API_CONNECTOR = 'data_api_connector'
    DATA_ANALYZER = 'data_analyzer'
    VISUALIZER = 'statistical_visualizer'
    SLACK_NOTIFIER = 'slack_notifier'
    FILE_READER = 'file_reader'
    JSON_XML_PARSER = 'json_xml_parser'
    DOCUMENT_RETRIEVER = 'document_retriever'


# 1. TOOL I/O Schemas
# ----------------------------------------------------

class ToolOutputBase(BaseModel):
    """Base schema for all Tool outputs (for consistent response envelope)."""
    status: str = 'success'
    result: Any

# --- Input Schemas ---
class ToolInputBase(BaseModel):
    """Base schema for all Tool inputs (used by Agent to format calls)."""
    tool_name: ToolName

class SQLQueryInput(ToolInputBase):
    """Specific input schema for the SQL Execution Tool."""
    tool_name: ToolName = ToolName.SQL_EXECUTOR
    sql_query: str = Field(
        ..., 
        description="The SELECT query to execute against the database. MUST be a read-only query."
    )

# 🚨 INPUT: Data API Connector (data_api_connector.py)
class APIConnectorInput(ToolInputBase):
    tool_name: ToolName = ToolName.DATA_API_CONNECTOR
    endpoint_url: HttpUrl = Field(..., description="The full URL of the API endpoint to query.")
    params: Optional[Dict[str, Any]] = Field(None, description="Optional: Dictionary of query parameters.")

# 🚨 INPUT: Data Analyzer (data_analyzer_tool.py)
class AnalysisInput(ToolInputBase):
    tool_name: ToolName = ToolName.DATA_ANALYZER
    data: List[Dict] = Field(..., description="The raw list of dictionaries/JSON data to analyze.")
    analysis_type: str = Field(..., description="The type of analysis to perform (e.g., 'calculate_mean', 'check_outliers').")
    target_column: str = Field(..., description="The column name to perform numerical analysis on.")
    
# 🚨 INPUT: Statistical Visualizer (statistical_visualizer.py)
class VisualizerInput(ToolInputBase):
    tool_name: ToolName = ToolName.VISUALIZER
    data: List[Dict] = Field(..., description="The raw list of dictionaries/JSON data to visualize.")
    chart_type: str = Field(..., description="The type of chart required (e.g., 'bar', 'line', 'scatter').")
    x_axis: str = Field(..., description="The column name for the X-axis.")
    y_axis: Optional[str] = Field(None, description="The column name for the Y-axis.")

# 🚨 INPUT: Slack Notifier (slack_notifier.py)
class SlackInput(ToolInputBase):
    tool_name: ToolName = ToolName.SLACK_NOTIFIER
    channel: str = Field(..., description="The Slack channel ID or name (e.g., #mlops-alerts).")
    message: str = Field(..., description="The text content of the notification to send.")

# 🚨 INPUT: File Reader (file_reader.py)
class FileReaderInput(ToolInputBase):
    tool_name: ToolName = ToolName.FILE_READER
    file_uri: str = Field(..., description="The URI (local path, S3, or GCS URL) of the file to read.")
    max_bytes: PositiveInt = Field(1048576, description="Maximum number of bytes to read (1MB limit for safety).")

# 🚨 INPUT: JSON/XML Parser (json_xml_parser.py)
class ParserInput(ToolInputBase):
    tool_name: ToolName = ToolName.JSON_XML_PARSER
    raw_data: str = Field(..., description="The raw JSON or XML string to parse.")
    data_type: str = Field(..., description="The type of data to parse ('json' or 'xml').")

# 🚨 INPUT: Document Retriever (document_retriever_tool.py)
class RetrievalInput(ToolInputBase):
    tool_name: ToolName = ToolName.DOCUMENT_RETRIEVER
    query: str = Field(..., description="The natural language query to search internal documents.")
    policy_type: Optional[str] = Field(None, description="Optional: Filter search to a specific policy type.")
    
# --- Output Schemas (Được dùng để validate kết quả Tool trả về) ---
class SQLQueryOutput(ToolOutputBase):
    """Specific output schema for the SQL Execution Tool results."""
    query_result: List[Dict[str, Any]] = Field(
        ...,
        description="The list of rows returned from the database query."
    )
    rows_returned: int = Field(
        ...,
        description="The number of rows returned."
    )

# 🚨 OUTPUT: API Connector Output
class APIConnectorOutput(ToolOutputBase):
    status_code: int = Field(..., description="The HTTP status code.")
    data: Dict[str, Any] = Field(..., description="The JSON data returned from the API.")

# 🚨 OUTPUT: Data Analyzer Output
class AnalysisOutput(ToolOutputBase):
    analysis_result: Dict[str, Any] = Field(..., description="The structured result of the statistical analysis.")
    summary: str = Field(..., description="A plain language summary of the findings.")
    
# 🚨 OUTPUT: Visualizer Output
class VisualizerOutput(ToolOutputBase):
    python_code: str = Field(..., description="The generated Python code snippet for the visualization (e.g., Plotly code).")

# 🚨 OUTPUT: Slack Output
class SlackOutput(ToolOutputBase):
    response_message: str = Field(..., description="The response message from the Slack API.")
    
# 🚨 OUTPUT: File Reader Output
class FileReaderOutput(ToolOutputBase):
    content: str = Field(..., description="The read content of the file (truncated if over limit).")
    size_bytes: int = Field(..., description="The size of the content read.")

# 🚨 OUTPUT: JSON/XML Parser Output
class ParserOutput(ToolOutputBase):
    structured_data: Union[Dict, List, str] = Field(..., description="The parsed Python dictionary, list, or XML string representation.")

# 🚨 OUTPUT: Document Retrieval Output
class RetrievedDocument(BaseModel):
    source_id: str
    snippet: str
    score: float
    
class RetrievalOutput(ToolOutputBase):
    retrieved_documents: List[RetrievedDocument] = Field(..., description="A list of relevant document snippets.")

# --- 2. LLM Schemas (Hardening Resilience) ---
class LLMBaseConfig(BaseModel):
    type: LLMType
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    max_tokens: Optional[PositiveInt] = None
    
class OpenAILLMConfig(LLMBaseConfig):
    api_key: SecretStr
    model_name: str

class HuggingFaceLLMConfig(LLMBaseConfig):
    model_path: Path # Yêu cầu đường dẫn tồn tại (Path Validation)

class LLMServiceConfig(BaseModel):
    """Schema chính để khởi tạo LLMWrapper (Primary & Fallback)."""
    primary: OpenAILLMConfig # Hoặc bất kỳ LLM nào
    fallback: Optional[HuggingFaceLLMConfig] = None


# --- 2. Tool Schemas (Hardening Security) ---
class ToolBaseConfig(BaseModel):
    type: ToolName
    description: str

class SQLToolConfig(ToolBaseConfig):
    db_connection_string: SecretStr # Sử dụng SecretStr cho kết nối DB
    # Thêm schema cho các tham số khác nếu cần

class EmailToolConfig(ToolBaseConfig):
    smtp_server: str
    password_secret_name: str # Tên secret chứa mật khẩu
    port: PositiveInt
    
class SlackToolConfig(ToolBaseConfig):
    slack_webhook_url: SecretStr # URL webhook Slack

# --- 3. Agent Schemas (Hardening Cost Control) ---
class AgentBaseConfig(BaseModel):
    type: str # Ví dụ: "react", "crewai"
    llm_config_key: str = Field(..., description="Key mapping to LLMFactory configuration.")
    tools: List[ToolName] # List các ToolName được phép truy cập
    max_loops: PositiveInt = 10 # Giới hạn vòng lặp
    temperature: float = Field(0.7, ge=0.0, le=1.0)

class ReActAgentConfig(AgentBaseConfig):
    # Thêm các tham số riêng cho ReAct
    pass 


# 🚨 CONFIG: Planning Agent (Không cần Tools)
class PlanningAgentConfig(AgentBaseConfig):
    max_loops: PositiveInt = 1 # Planning chỉ là 1 bước suy luận, không có loop
    tools: List[ToolName] = Field(default_factory=list, description="Planning Agent does not require tools.")
    temperature: float = Field(0.1, ge=0.0, le=1.0) # Nhiệt độ thấp cho tính logic

# 🚨 CONFIG: Safety/Critic Agents (Chỉ cần LLM)
class CriticAgentConfig(AgentBaseConfig):
    max_loops: PositiveInt = 1 # Chỉ 1 lần chạy
    tools: List[ToolName] = Field(default_factory=list, description="Critic Agents do not use tools.")
    policy_documents: Optional[str] = Field(None, description="Contextual policy documents for review.")
    temperature: float = Field(0.0, ge=0.0, le=1.0) # Cực kỳ thấp cho tính khách quan

# 🚨 CONFIG: Supervisor Agent (Cần biết Workers và max_steps)
class SupervisorAgentConfig(AgentBaseConfig):
    # Supervisor không cần tools (vì nó giao việc), nhưng nó cần biết Workers
    tools: List[ToolName] = Field(default_factory=list, description="Supervisor Agent delegates tool execution.")
    worker_keys: List[str] = Field(..., description="List of keys for worker agents managed by this supervisor.")
    max_orchestration_steps: PositiveInt = Field(20, description="Max steps in the overall workflow.")
    temperature: float = Field(0.5, ge=0.0, le=1.0)

# 🚨 CONFIG: Tool Coordinator Agent (Cần biết các Tools tiện ích)
class ToolCoordinatorConfig(AgentBaseConfig):
    max_loops: PositiveInt = 1
    tools: List[ToolName] = Field(..., description="List of ALL worker tools managed by the coordinator.")
    audit_tool_key: str = Field(..., description="Key mapping to AuditTool instance.")
    cache_tool_key: str = Field(..., description="Key mapping to CacheTool instance.")
    # Không cần LLM cho Tool Coordinator (nó chỉ là logic cổng), nhưng ta giữ field LLM cho contract nếu nó cần logic LLM sau này
    
# 🚨 CONFIG: Meta Agent (Giám sát)
class MetaAgentConfig(AgentBaseConfig):
    max_loops: PositiveInt = 1
    tools: List[ToolName] = Field(default_factory=list, description="Meta Agent does not use tools.")
    monitoring_interval_sec: PositiveInt = Field(3600, description="Interval for performance monitoring.")

# --- 4. Prompt Schemas (Hardening Validation) ---
class PromptBaseConfig(BaseModel):
    type: str
    template: str
    variables: List[str] # Danh sách các biến cần được điền vào template

class RAGPromptConfig(PromptBaseConfig):
    pass # Kế thừa và sử dụng cho RAGPrompt

# --- 5. Evaluator Schemas (Hardening Quality Assurance) ---
class EvaluatorEntry(BaseModel):
    type: str # Ví dụ: "safety", "hallucination"
    enabled: bool
    context: Dict[str, Any] = {} # Tham số tùy chỉnh (ví dụ: ground_truth_key)

class EvaluatorConfigSchema(BaseModel):
    evaluators: List[EvaluatorEntry]
    

# --- The Central Registry Class (CRITICAL HARDENING) ---
class SchemaRegistry:
    """
    A centralized registry providing access to all validated Pydantic schemas.
    Nó là Single Source of Truth cho Agent về cách gọi các Tools.
    """
    # 🚨 CẬP NHẬT: Thêm tất cả Input Schemas vào Registry
    TOOL_INPUT_MAP: Dict[ToolName, BaseModel] = {
        ToolName.SQL_EXECUTOR: SQLQueryInput,
        ToolName.DATA_API_CONNECTOR: APIConnectorInput,
        ToolName.DATA_ANALYZER: AnalysisInput,
        ToolName.VISUALIZER: VisualizerInput,
        ToolName.SLACK_NOTIFIER: SlackInput,
        ToolName.FILE_READER: FileReaderInput,
        ToolName.JSON_XML_PARSER: ParserInput,
        ToolName.DOCUMENT_RETRIEVER: RetrievalInput,
        # Thêm các tool khác (Email, Risk, Calculator)
    }
    
    @staticmethod
    def get_tool_input_schema(tool_name: str) -> BaseModel:
        """Retrieves the specific Pydantic schema for a given tool."""
        if tool_name not in SchemaRegistry.TOOL_INPUT_MAP:
            # Thêm logic để tra cứu các Tool khác nếu cần (ví dụ: Risk Tool)
            raise ValueError(f"Schema not found for tool: {tool_name}")
        return SchemaRegistry.TOOL_INPUT_MAP[tool_name]
    
    
    # 🚨 CẬP NHẬT: THÊM REGISTRY CHO AGENT CONFIG
    AGENT_CONFIG_MAP: Dict[str, type[BaseModel]] = {
        # Framework
        "react": ReActAgentConfig,
        "planning": PlanningAgentConfig,
        # Governance
        "supervisor": SupervisorAgentConfig,
        "safety": CriticAgentConfig, # Safety và Critic dùng chung cấu trúc cơ bản
        "tool_coordinator": ToolCoordinatorConfig,
        "meta": MetaAgentConfig,
        "retrieval": ReActAgentConfig, # Retrieval Agent kế thừa ReAct
        # Domain
        "risk_manager": ReActAgentConfig, # Risk Manager kế thừa ReAct
        "compliance_critic": CriticAgentConfig,
    }
    
    @staticmethod
    def get_agent_config_schema(agent_name: str) -> BaseModel:
        """Retrieves the specific Pydantic config schema for a given agent."""
        agent_name = agent_name.lower()
        if agent_name not in SchemaRegistry.AGENT_CONFIG_MAP:
            raise ValueError(f"Config Schema not found for agent: {agent_name}")
        return SchemaRegistry.AGENT_CONFIG_MAP[agent_name]