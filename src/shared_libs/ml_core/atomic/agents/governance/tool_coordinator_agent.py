# shared_libs/atomic/agents/governance/tool_coordinator_agent.py

from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_llm import BaseLLM
from shared_libs.base.base_tool import BaseTool
from shared_libs.utils.exceptions import SecurityError, ToolExecutionError
from typing import Dict, Any, Optional
import asyncio

# 🚨 Imports các Service Adapters mới
from shared_libs.service_adapters.data_access_service import DataAccessService
from shared_libs.service_adapters.compute_service import ComputeService

class ToolCoordinatorAgent(BaseAgent):
    """
    Agent chuyên biệt quản lý và điều phối tất cả các lệnh gọi Tool từ các Worker Agent. 
    Nó kiểm soát quyền truy cập (ACL), quản lý caching, và ghi lại nhật ký kiểm toán (audit log),
    đồng thời ủy quyền thực thi Tool cho các Service Adapters chuyên biệt (DataAccess/Compute).
    """

    @property
    def name(self) -> str:
        return "tool_coordinator_agent"

    @property
    def description(self) -> str:
        return "Centralized coordinator for all tool calls. Manages Access Control (ACL), Caching, Auditing, and delegates execution to specialized DataAccess and Compute services for performance and security."

    def __init__(self, 
                 llm: BaseLLM, 
                 available_tools: Dict[str, BaseTool], 
                 audit_tool: BaseTool, 
                 cache_tool: BaseTool,
                 data_access_service: DataAccessService, # 🚨 Service Adapter 1
                 compute_service: ComputeService,       # 🚨 Service Adapter 2
                ):
        """
        Khởi tạo Coordinator với các Tools tiện ích và các Service Adapters.
        """
        self.llm = llm
        self.available_tools = available_tools
        self.audit_tool = audit_tool
        self.cache_tool = cache_tool
        
        # 🚨 Lưu các Service Adapters để ủy quyền
        self.data_access_service = data_access_service
        self.compute_service = compute_service
        
        # Định nghĩa các Tools được thực thi trực tiếp (External I/O đơn giản/Governance)
        self.direct_execution_tools = ["audit_tool", "cache_tool", "slack_notifier", "email_tool"]
        
        # Lấy danh sách tên Tools cho mục đích kiểm tra nhanh
        self.data_access_tools = list(data_access_service.data_access_tools.keys())
        self.compute_tools = list(compute_service.compute_tools.keys())

    # --- Core Tool Coordination Method (Asynchronous) ---
    async def async_execute_tool_call(self, agent_name: str, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Thực hiện một lệnh gọi Tool sau khi kiểm tra ACL và Cache, sau đó ủy quyền thực thi.
        """
        
        # 1. Kiểm tra Quyền truy cập (ACL Mock)
        if not self._check_acl(agent_name, tool_name):
            error_msg = f"Security Error: Agent '{agent_name}' is not authorized to call tool '{tool_name}'."
            await self._record_audit("ACL_DENIED", agent_name, tool_name)
            raise SecurityError(error_msg)

        # Kiểm tra Tool có tồn tại trong hệ thống Tool pool nào không
        if tool_name not in self.available_tools:
            raise ToolExecutionError(f"Tool '{tool_name}' not registered in any service pool.")


        # 2. Kiểm tra Cache (Dùng chung cho tất cả Tools)
        cache_key = f"{tool_name}:{str(tool_input)}"
        try:
            cached_result = await self.cache_tool.async_run({"action": "GET", "key": cache_key})
            if cached_result and cached_result is not None:
                await self._record_audit("TOOL_CACHE_HIT", agent_name, tool_name)
                return f"Observation (Cached): {cached_result}"
        except Exception:
            pass # Bỏ qua lỗi cache, tiếp tục thực thi

        # 3. THỰC THI & ỦY QUYỀN (Delegation and Execution)
        await self._record_audit("TOOL_EXECUTE_START", agent_name, tool_name, tool_input)
        
        try:
            if tool_name in self.data_access_tools:
                # 🚨 ỦY QUYỀN cho Data Access Service (I/O nặng)
                observation = await self.data_access_service.execute_async(tool_name, tool_input)
                
            elif tool_name in self.compute_tools:
                # 🚨 ỦY QUYỀN cho Compute Service (CPU-Bound)
                observation = await self.compute_service.execute_async(tool_name, tool_input)

            elif tool_name in self.direct_execution_tools:
                # Thực thi TRỰC TIẾP cho các Tools Governance/External I/O đơn giản
                tool = self.available_tools[tool_name]
                observation = await tool.async_run(tool_input)
                
            else:
                raise ToolExecutionError(f"Tool '{tool_name}' not mapped to any specialized execution service.")

            # 4. Lưu Cache và Audit Thành công
            await self.cache_tool.async_run({"action": "SET", "key": cache_key, "value": observation})
            await self._record_audit("TOOL_EXECUTE_SUCCESS", agent_name, tool_name)
            
            # Trả về kết quả từ Service Adapter/Tool
            # Giả định Service Adapter trả về dict, cần convert sang string cho Agent Observation
            return f"Observation: {observation}"
            
        except Exception as e:
            await self._record_audit("TOOL_EXECUTE_FAILURE", agent_name, tool_name, error=str(e))
            raise ToolExecutionError(f"Execution of tool '{tool_name}' failed: {e}")

    # --- Internal ACL Mock ---
    def _check_acl(self, agent_name: str, tool_name: str) -> bool:
        """Logic kiểm tra quyền truy cập giả định."""
        if agent_name == "compliance_critic_agent" and ("sql" in tool_name or "delete" in tool_name):
            return False
        return True

    async def _record_audit(self, event: str, agent: str, tool: str, input: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Helper để ghi Audit Log thông qua AuditTool."""
        audit_data = {"event": event, "agent": agent, "tool": tool}
        if input:
            audit_data["input"] = input
        if error:
            audit_data["error"] = error
        await self.audit_tool.async_run({"action": "LOG", "data": audit_data})

    # --- BaseAgent Abstract Methods (Hoàn thiện Contract) ---
    def loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        raise NotImplementedError("ToolCoordinator Agent is managed externally for tool calls. Use async_execute_tool_call.")
    
    async def async_loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        raise NotImplementedError("ToolCoordinator Agent is managed externally for tool calls. Use async_execute_tool_call.")

    def plan(self, user_input: str, context: Dict[str, Any]) -> str:
      raise NotImplementedError("ToolCoordinator Agent is not for planning.")
    
    def act(self, action: str, **kwargs) -> Any:
      raise NotImplementedError("ToolCoordinator Agent does not perform external actions.")
    
    def observe(self, observation: Any) -> None:
      pass