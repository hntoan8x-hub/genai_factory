# shared_libs/factory/agent_factory.py (FINAL HARDENED VERSION - Tích hợp Phân tầng)

from typing import Dict, Any, Union, List, Optional
from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_llm import BaseLLM
from shared_libs.base.base_tool import BaseTool
from shared_libs.utils.exceptions import GenAIFactoryError

# --- Import Pattern Agents (Framework/Tầng 1) ---
from shared_libs.atomic.agents.framework.react_agent import ReActAgent
from shared_libs.atomic.agents.framework.planning_agent import PlanningAgent
from shared_libs.atomic.agents.framework.reflexion_agent import ReflexionAgent
from shared_libs.atomic.agents.framework.autogen_agent import AutoGenAgent
from shared_libs.atomic.agents.framework.crewai_agent import CrewAIAgent

# --- Import Governance Agents (Oversight/Tầng 3) ---
from shared_libs.atomic.agents.governance.supervisor_agent import SupervisorAgent
from shared_libs.atomic.agents.governance.safety_agent import SafetyAgent
from shared_libs.atomic.agents.governance.retrieval_agent import RetrievalAgent
from shared_libs.atomic.agents.governance.tool_coordinator_agent import ToolCoordinatorAgent
from shared_libs.atomic.agents.governance.meta_agent import MetaAgent

# --- Import Domain Agents (Specialized/Tầng 2) ---
from domain_models.genai_assistant.agents.compliance_critic_agent import ComplianceCriticAgent
from domain_models.genai_assistant.agents.risk_manager_agent import RiskManagerAgent

# HARDENING: Import các Schema Agent (Giả định đã có)
from shared_libs.configs.schemas import AgentBaseConfig, ReActAgentConfig # Thêm các Config Models cần thiết

# Định nghĩa Union cho các loại config model được chấp nhận
AgentConfigModel = Union[ReActAgentConfig, AgentBaseConfig] 

class AgentFactory:
    """
    Factory Class khởi tạo Agent, sử dụng Registry và Dictionary Unpacking 
    để hỗ trợ kiến trúc phân tầng (Framework, Governance, Domain).
    """

    def __init__(self):
        # REGISTRY CHUNG CHO TOÀN BỘ FACTORY
        self._agent_types: Dict[str, type[BaseAgent]] = {
            # 1. FRAMEWORK (Tầng 1)
            "planning": PlanningAgent,
            "reflexion": ReflexionAgent,
            "react": ReActAgent,
            "autogen": AutoGenAgent,
            "crewai": CrewAIAgent,
            
            # 2. GOVERNANCE (Tầng 3)
            "supervisor": SupervisorAgent,
            "safety": SafetyAgent,
            "retrieval": RetrievalAgent, # Vị trí Governance vì nó chuyên môn hóa Tool
            "tool_coordinator": ToolCoordinatorAgent,
            "meta": MetaAgent,
            
            # 3. DOMAIN (Tầng 2)
            "compliance_critic": ComplianceCriticAgent,
            "risk_manager": RiskManagerAgent,
        }
        
    def _extract_params(self, agent_name: str, llm: BaseLLM, tools: List[BaseTool], config_model: Optional[AgentConfigModel], **kwargs) -> Dict[str, Any]:
        """
        Helper function để chuẩn bị dictionary tham số khởi tạo cho Agent.
        """
        params = {"llm": llm, **kwargs}
        
        # 1. Xử lý Tools: Chỉ truyền Tools nếu Agent cần (Hầu hết các Worker Agent và ReAct)
        # Các Oversight Agents (Safety, Planning, Reflexion, Meta) thường không cần Tools
        if agent_name in ["react", "autogen", "crewai", "risk_manager", "retrieval", "tool_coordinator"]:
            params["tools"] = tools

        # 2. Xử lý Config Model (Nếu có)
        if config_model:
            # Chuyển Pydantic model thành dict, loại bỏ các giá trị mặc định nếu cần
            config_dict = config_model.model_dump(exclude_none=True)
            
            # Hợp nhất config_dict vào params, ưu tiên tham số đã có (như llm)
            # **Chú ý**: 'tools' và 'llm' nên được quản lý riêng
            for k, v in config_dict.items():
                if k not in ["tools", "llm"]: 
                    params[k] = v
        
        # 3. Xử lý tham số chuyên biệt cho Supervisor/Coordinator
        # Các Agent này cần các instance Tool/Agent khác được truyền vào
        if agent_name == "tool_coordinator":
            # Yêu cầu tools là Dict[str, BaseTool] chứ không phải List
            params["available_tools"] = {t.name: t for t in tools}
            # Giả định audit_tool và cache_tool được truyền trong kwargs từ Pipeline/Orchestrator
            
        elif agent_name == "supervisor":
             # Giả định worker_agents (Dict[str, BaseAgent]) được truyền trong kwargs
             pass 

        return params


    def build(self, agent_name: str, llm: BaseLLM, tools: List[BaseTool] = [], config_model: Optional[AgentConfigModel] = None, **kwargs) -> BaseAgent:
        """
        Builds an Agent instance by name, LLM, Tools, và Config Model.
        """
        agent_type = agent_name.lower()
        
        if agent_type not in self._agent_types:
            raise ValueError(f"Unsupported Agent type: {agent_type}. Supported types are: {list(self._agent_types.keys())}")
        
        agent_class = self._agent_types[agent_type]
        
        # Lấy tất cả các tham số cần thiết
        try:
            params = self._extract_params(agent_type, llm, tools, config_model, **kwargs)
        except Exception as e:
            raise GenAIFactoryError(f"Error preparing parameters for Agent '{agent_type}': {e}")

        # --- LOGIC KHỞI TẠO CUỐI CÙNG (Dùng Unpacking) ---
        try:
            # 🚨 CẬP NHẬT CỐT LÕI: Dùng Dictionary Unpacking để khởi tạo linh hoạt
            return agent_class(**params)
            
        except TypeError as e:
            # Bắt lỗi nếu các tham số không khớp với __init__ của Agent
            required_args = list(agent_class.__init__.__code__.co_varnames)[1:]
            raise TypeError(f"Error initializing Agent '{agent_type}': Parameters mismatch. Expected: {required_args}. Provided (partial): {params.keys()}. Detail: {e}")
        except Exception as e:
            raise GenAIFactoryError(f"Unexpected error during Agent '{agent_type}' initialization: {e}")