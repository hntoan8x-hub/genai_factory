# src/shared_libs/logging/audit_logger.py (FINAL PRODUCTION CODE)

import logging
import time
import asyncio
from typing import Dict, Any, Optional

# Import Contracts và Schema
from shared_libs.logging.contracts.base_audit_logger import BaseAuditLogger 
from shared_libs.logging.configs.audit_schema import AuditConfigSchema 
from shared_libs.monitoring.contracts.base_alert_adapter import BaseAlertAdapter # Sử dụng Contract, không phải Implementation cụ thể

# Cấu hình logger audit chuyên biệt
# CRITICAL: Đảm bảo logger này được cấu hình để ghi ra định dạng JSON/Structured Log
audit_logger = logging.getLogger("AUDIT_TRAIL")

class AuditLogger(BaseAuditLogger):
    """
    Records immutable, auditable events for security and compliance purposes. 
    Implements BaseAuditLogger contract. (CRITICAL GOVERNANCE)
    """

    def __init__(self, config: Dict[str, Any], alert_adapter: BaseAlertAdapter):
        """
        Khởi tạo logger bằng Dependency Injection.
        Args:
            config (Dict[str, Any]): Cấu hình logger, phải hợp lệ với AuditConfigSchema.
            alert_adapter (BaseAlertAdapter): Adapter để kích hoạt cảnh báo bảo mật.
        """
        super().__init__(config)
        
        # Hardening 1: Validate Config Schema
        self.audit_conf = AuditConfigSchema.model_validate(config)
        
        # Hardening 2: Dependency Injection cho Alert Adapter
        self.alert_adapter = alert_adapter
        
        logger.info(f"Audit Logger initialized. Compliance Level: {self.audit_conf.compliance_level}")

    def _log_event(self, event_type: str, request_id: str, user_id: str, severity: str = "INFO", data: Dict[str, Any] = None):
        """Internal helper để cấu trúc và ghi log entry."""
        log_entry = {
            "timestamp": time.time(),
            "request_id": request_id,
            "user_id": user_id,
            "event_type": event_type,
            "severity": severity,
            "data": data if data is not None else {}
        }
        
        # Ghi log: Dùng .info/.critical tùy thuộc severity để dễ dàng tìm kiếm/filter
        if severity in ["CRITICAL", "HIGH"]:
            audit_logger.critical("Audit Event", extra=log_entry)
        else:
            audit_logger.info("Audit Event", extra=log_entry)

    def log_request_start(self, request_id: str, user_id: str, query: str):
        """Logs the start of a user request, bao gồm truy vấn ban đầu."""
        self._log_event(
            "request_start", request_id, user_id, "INFO", 
            {"query": query}
        )

    async def async_log_security_event(self, request_id: str, user_id: str, event_details: str, severity: str = "HIGH"):
        """
        Logs security events (ví dụ: Prompt Injection, PII leakage) và 
        kích hoạt cảnh báo tức thời nếu cần.
        """
        self._log_event(
            "security_violation", request_id, user_id, severity, 
            {"detail": event_details}
        )
        
        # 🚨 Kích hoạt cảnh báo tức thời qua Adapter
        if severity in ["CRITICAL", "HIGH"]:
            await self.alert_adapter.async_send_alert(
                message=f"AUDIT VIOLATION: {event_details}", 
                severity=severity,
                context={"request_id": request_id, "user_id": user_id}
            )

    def log_final_response(self, request_id: str, user_id: str, final_status: str, llm_cost: float):
        """Logs the final outcome of the request, bao gồm chi phí cuối cùng."""
        self._log_event(
            "request_end", request_id, user_id, "INFO", 
            {
                "final_status": final_status, 
                "llm_cost_usd": round(llm_cost, 6)
            }
        )