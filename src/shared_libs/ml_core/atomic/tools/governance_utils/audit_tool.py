# shared_libs/atomic/tools/governance_utils/audit_tool.py

from shared_libs.base.base_tool import BaseTool
from shared_libs.configs.schemas import AuditToolConfig # Import Config
from typing import Dict, Any, Optional
import asyncio
import logging
import json
import time

# Sử dụng logger chuyên biệt cho Audit
audit_logger = logging.getLogger("GOVERNANCE_AUDIT")

class AuditTool(BaseTool):
    """
    Tool chuyên biệt ghi lại các sự kiện kiểm toán (Audit Trail) bất biến 
    cho mục đích tuân thủ và an ninh. (CRITICAL GOVERNANCE TOOL)
    """

    @property
    def name(self) -> str:
        return "audit_tool"

    @property
    def description(self) -> str:
        return "Records critical events (tool calls, security checks, final decisions) into the immutable audit log sink."

    def __init__(self, log_sink_uri: str, **kwargs):
        """
        Khởi tạo Audit Tool.
        Args:
            log_sink_uri (str): URI của dịch vụ ghi nhật ký tập trung (ví dụ: ELK endpoint).
        """
        super().__init__(**kwargs)
        self.log_sink_uri = log_sink_uri
        # Trong môi trường production, Audit Tool sẽ khởi tạo kết nối tới log_sink_uri tại đây
        self._is_ready = True
        
        # Cấu hình logger cơ bản (giả định)
        if not audit_logger.handlers:
             audit_logger.setLevel(logging.INFO)

    def _log_internal(self, event_data: Dict[str, Any]):
        """Helper đồng bộ để định dạng và ghi log."""
        log_entry = {
            "timestamp": time.time(),
            "event_id": str(uuid.uuid4()), # Giả định UUID được import
            "component": "ToolCoordinator",
            "source_uri": self.log_sink_uri,
            "data": event_data
        }
        
        # Trong thực tế, đây sẽ là lệnh POST HTTP tới log_sink_uri
        # Tạm thời ghi vào console/file log
        audit_logger.info("AUDIT EVENT LOGGED", extra=log_entry)

    async def async_run(self, tool_input: Dict[str, Any]) -> str:
        """
        Thực hiện ghi lại một sự kiện Audit.
        
        Tool Input Format (Ví dụ):
        {
            "action": "LOG",
            "data": {
                "event": "TOOL_EXECUTE_START",
                "agent": "risk_manager",
                "tool": "sql_query_executor",
                "input": {...}
            }
        }
        """
        action = tool_input.get("action", "LOG")
        data = tool_input.get("data", {})
        
        if action.upper() != "LOG" or not data:
            return "Observation: Audit Tool only supports 'LOG' action with 'data'."

        # Thực hiện tác vụ I/O đồng bộ trên một executor (không chặn async loop)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._log_internal, data)
        
        return "Observation: Audit event successfully logged."

    def run(self, tool_input: Dict[str, Any]) -> str:
        """Phương thức đồng bộ (chỉ để hoàn thành BaseTool contract, khuyến khích dùng async)."""
        raise NotImplementedError("Use the asynchronous method 'async_run' for Audit logging.")