# GenAI_Factory/src/domain_models/genai_assistant/services/tool_service.py

import logging
from typing import Any, Dict, List, Optional
from shared_libs.base.base_tool import BaseTool
from shared_libs.factory.tool_factory import ToolFactory
from shared_libs.utils.exceptions import SecurityError, ToolExecutionError, GenAIFactoryError
from domain_models.genai_assistant.schemas.tool_schema import ToolInputSchema, ToolOutputSchema # Hardened Schemas

logger = logging.getLogger(__name__)

class ToolService:
    """
    Dynamic registry and router for available tools.
    Enforces security checks (Role-Based Access Control) and data validation 
    before executing any tool. (CRITICAL HARDENING)
    """

    def __init__(self, tool_configs: Dict[str, Any]):
        """Initializes the registry by creating tool instances via ToolFactory."""
        self.tool_registry: Dict[str, BaseTool] = {}
        
        # Hardening: Access Control List (ACL) cho các công cụ nhạy cảm
        # Maps tool name to a list of required user roles/groups
        self.access_control: Dict[str, List[str]] = {
            "sql_query_executor": ["analyst_group", "admin", "risk_analyst"],
            "email_tool": ["authenticated_users", "manager"],
            "financial_risk_model": ["risk_analyst"], 
        }

        # 1. Initialize Tool Registry
        for tool_name, config in tool_configs.items():
            try:
                # ToolFactory handles the creation, injecting necessary configs (DB, API keys)
                tool_instance = ToolFactory.build(config)
                self.tool_registry[tool_instance.name] = tool_instance 
                logger.info(f"Tool registered: {tool_instance.name}")
            except Exception as e:
                # Ghi log lỗi và raise nếu đó là lỗi nghiêm trọng, hoặc tiếp tục nếu là lỗi tải tool đơn lẻ
                logger.error(f"Failed to initialize tool {tool_name}: {e}")
                # Trong Production: Thường raise GenAIFactoryError để báo lỗi khởi tạo fatal
                pass
            

    def get_tool(self, tool_name: str) -> BaseTool:
        """Retrieves a tool instance by name."""
        if tool_name not in self.tool_registry:
            raise ToolExecutionError(f"Tool '{tool_name}' not found in registry.")
        return self.tool_registry[tool_name]

    def _check_access(self, tool_name: str, user_role: str):
        """
        Checks if the user role has permission to use the tool. (CRITICAL HARDENING)
        This prevents unauthorized access to sensitive actions like SQL/Email.
        """
        allowed_roles = self.access_control.get(tool_name)
        
        # Nếu không có ACL được định nghĩa, công cụ được coi là công khai
        if allowed_roles is None:
            return 

        # Kiểm tra xem vai trò của người dùng có nằm trong danh sách cho phép không
        if user_role not in allowed_roles:
            logger.warning(f"ACCESS DENIED: Role '{user_role}' denied use of sensitive tool '{tool_name}'.")
            # Log Audit Security Violation tại đây
            raise SecurityError(
                f"Access denied: Role '{user_role}' cannot use sensitive tool '{tool_name}'."
            )

    async def async_execute_tool(self, tool_name: str, input_data: Dict[str, Any], user_role: str) -> ToolOutputSchema:
        """
        Asynchronously executes a tool after performing access control and input validation.
        This is the preferred method for Agent orchestration.
        
        Args:
            tool_name (str): Tên công cụ cần thực thi.
            input_data (Dict[str, Any]): Dữ liệu đầu vào (từ Agent).
            user_role (str): Vai trò của người dùng (từ AuthZ).
            
        Returns:
            ToolOutputSchema: Output có cấu trúc.
        """
        tool = self.get_tool(tool_name)
        
        # 1. Access Control Check (CRITICAL SECURITY GATE)
        self._check_access(tool.name, user_role)

        # 2. Input Validation (Schema Enforcement)
        try:
            # Xác thực dữ liệu thô từ Agent bằng ToolInputSchema
            validated_input = ToolInputSchema(tool_name=tool_name, arguments=input_data)
        except Exception as e:
            # Nếu Agent đưa ra input không hợp lệ, trả về lỗi có cấu trúc
            logger.warning(f"Tool input validation failed for {tool_name}: {e}")
            return ToolOutputSchema(output_data=None, success=False, error_message=f"Input validation error: {e}")

        # 3. Execution (Uses the hardened async_run method)
        logger.info(f"Executing tool '{tool_name}' for role '{user_role}'.")
        try:
            # BaseTool's async_run nhận arguments đã được xác thực
            raw_result = await tool.async_run(validated_input.arguments)
            
            # 4. Output Validation (Schema Enforcement)
            # Giả định raw_result có thể được chuyển đổi thành output_data trong schema
            return ToolOutputSchema(output_data=raw_result, success=True, error_message=None)
            
        except Exception as e:
            # Bắt lỗi thực thi tool và trả về ToolOutputSchema có cấu trúc
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return ToolOutputSchema(output_data=None, success=False, error_message=f"Tool execution failed: {e.__class__.__name__}")