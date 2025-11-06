# shared_libs/configs/schemas/agent_config.py

from pydantic import BaseModel, Field, PositiveInt
from typing import List, Optional, Dict, Any
from shared_libs.configs.schemas import ToolName # Import Enums từ __init__.py

# --- 1. BASE CONFIG SCHEMAS (REQUIRED FOR ALL AGENTS) ---
class AgentBaseConfig(BaseModel):
    """Cấu hình cơ sở cho mọi loại Agent. Chứa các tham số kiểm soát nguồn lực chung."""
    type: str = Field(..., description="Loại Agent (ví dụ: 'react', 'supervisor').")
    llm_config_key: str = Field(..., description="Key mapping đến cấu hình LLM trong LLMFactory.")
    tools: List[ToolName] = Field(default_factory=list, description="Danh sách các Tool được cấp quyền truy cập.")
    max_loops: PositiveInt = Field(10, description="Giới hạn số bước thực thi (quan trọng cho kiểm soát chi phí).")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Tham số nhiệt độ của mô hình LLM.")
    
# --- 2. FRAMEWORK/EXECUTOR AGENT CONFIGS (Tầng 1 & 2) ---

class ReActAgentConfig(AgentBaseConfig):
    """
    Cấu hình cho ReActAgent. Được dùng cho các Agent kế thừa (RetrievalAgent, RiskManagerAgent).
    Kế thừa toàn bộ tham số kiểm soát từ AgentBaseConfig.
    """
    type: str = Field('react', description="Loại Agent là ReAct (Thought-Act-Observe).")
    
class PlanningAgentConfig(AgentBaseConfig):
    """Cấu hình cho PlanningAgent."""
    type: str = Field('planning')
    max_loops: PositiveInt = 1 # Planning chỉ là 1 bước suy luận
    temperature: float = Field(0.1, ge=0.0, le=1.0)
    tools: List[ToolName] = Field(default_factory=list, description="Planning Agent không sử dụng Tools.")

class CriticAgentConfig(AgentBaseConfig):
    """Cấu hình chung cho SafetyAgent, ReflexionAgent, ComplianceCriticAgent."""
    type: str = Field('critic')
    max_loops: PositiveInt = 1 # Chỉ 1 lần chạy kiểm tra
    temperature: float = Field(0.0, ge=0.0, le=1.0, description="Nhiệt độ bằng 0 cho tính khách quan tuyệt đối.")
    tools: List[ToolName] = Field(default_factory=list, description="Critic Agents không sử dụng Tools.")
    policy_documents: Optional[str] = Field(None, description="Tài liệu chính sách hoặc quy tắc để tham chiếu khi đánh giá.")

# --- 3. GOVERNANCE/OVERSIGHT AGENT CONFIGS (Tầng 3) ---

class SupervisorAgentConfig(AgentBaseConfig):
    """Cấu hình cho Supervisor Agent (Workflow Orchestrator)."""
    type: str = Field('supervisor')
    tools: List[ToolName] = Field(default_factory=list, description="Supervisor Agent giao việc, không tự thực thi Tools.")
    worker_keys: List[str] = Field(..., description="Danh sách các key định danh của Worker Agent được Supervisor này quản lý.")
    max_orchestration_steps: PositiveInt = Field(20, description="Giới hạn số bước trong toàn bộ quy trình điều phối.")
    temperature: float = Field(0.5, ge=0.0, le=1.0) # Nhiệt độ trung bình cho quyết định điều phối

class ToolCoordinatorConfig(AgentBaseConfig):
    """Cấu hình cho Tool Coordinator Agent (Access Control Gateway)."""
    type: str = Field('tool_coordinator')
    max_loops: PositiveInt = 1
    tools: List[ToolName] = Field(..., description="Danh sách ALL Tools nghiệp vụ được điều phối.")
    audit_tool_key: str = Field(..., description="Key mapping đến AuditTool instance.")
    cache_tool_key: str = Field(..., description="Key mapping đến CacheTool instance.")
    # LLM được giữ lại nhưng thường không dùng cho logic core

class MetaAgentConfig(AgentBaseConfig):
    """Cấu hình cho Meta Agent (Optimization Engine)."""
    type: str = Field('meta')
    max_loops: PositiveInt = 1
    tools: List[ToolName] = Field(default_factory=list, description="Meta Agent không sử dụng Tools.")
    temperature: float = Field(0.1, ge=0.0, le=1.0)
    monitoring_interval_sec: PositiveInt = Field(3600, description="Khoảng thời gian (giây) giữa các lần phân tích tối ưu hóa.")

# --- 4. REGISTRY AGENT CONFIG MAP (Sử dụng bởi SchemaRegistry trong __init__.py) ---
AGENT_CONFIG_MAP: Dict[str, type[BaseModel]] = {
    "react": ReActAgentConfig,
    "planning": PlanningAgentConfig,
    "reflexion": CriticAgentConfig,
    "supervisor": SupervisorAgentConfig,
    "safety": CriticAgentConfig, 
    "tool_coordinator": ToolCoordinatorConfig,
    "meta": MetaAgentConfig,
    "retrieval": ReActAgentConfig, 
    "risk_manager": ReActAgentConfig, 
    "compliance_critic": CriticAgentConfig,
}