# src/shared_libs/logging/contracts/base_audit_logger.py

import abc
from typing import Dict, Any, Optional
import asyncio

class BaseAuditLogger(abc.ABC):
    """
    Abstract Base Class (Contract) cho Audit Logger.
    """

    @abc.abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """Khởi tạo logger với cấu hình đã được xác thực (AuditConfigSchema)."""
        self.config = config
        pass

    @abc.abstractmethod
    def log_request_start(self, request_id: str, user_id: str, query: str):
        """Logs the start of a user request."""
        raise NotImplementedError

    @abc.abstractmethod
    async def async_log_security_event(self, request_id: str, user_id: str, event_details: str, severity: str):
        """Logs security events and triggers alert if configured."""
        raise NotImplementedError

    @abc.abstractmethod
    def log_final_response(self, request_id: str, user_id: str, final_status: str, llm_cost: float):
        """Logs the final outcome of the request."""
        raise NotImplementedError