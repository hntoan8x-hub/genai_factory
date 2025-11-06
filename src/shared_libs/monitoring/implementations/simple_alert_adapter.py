# src/shared_libs/monitoring/implementations/simple_alert_adapter.py (Đổi tên file cho rõ ràng)

import logging
import asyncio
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import requests 
from shared_libs.monitoring.contracts.base_alert_adapter import BaseAlertAdapter # Import Contract
# Import Schema đã tạo
from shared_libs.monitoring.configs.monitoring_schema import AlertConfigSchema 

logger = logging.getLogger(__name__)

# Hardening: Triển khai Contract và sử dụng Schema
class SimpleAlertAdapter(BaseAlertAdapter):
    """
    Adapter cho Slack/PagerDuty webhook. Sử dụng ThreadPoolExecutor để offload I/O.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Hardening 1: Xác thực config bằng Schema
        self.alert_conf = AlertConfigSchema.model_validate(config)
        
        self.webhook_url = str(self.alert_conf.webhook_url) # Lấy URL đã xác thực
        self.default_channel = self.alert_conf.default_channel
        
        # Hardening 2: Sử dụng max_workers từ Schema
        self.executor = ThreadPoolExecutor(max_workers=self.alert_conf.max_workers)

    def _send_alert_sync(self, message: str, severity: str, context: Optional[Dict[str, Any]]) -> bool:
        """Thực hiện HTTP POST cảnh báo đồng bộ trên executor."""
        
        # Tạo payload theo định dạng của hệ thống cảnh báo
        detail_context = "\n".join([f"  • {k}: {v}" for k, v in (context or {}).items()])
        
        payload = {
            "channel": self.default_channel,
            "text": f"🚨 [{severity.upper()} ALERT - GENAI SERVICE]\nDetail: {message}\n\n*Context:*\n{detail_context}",
        }
        
        try:
            # Hardening 3: Sử dụng timeout từ Schema
            response = requests.post(self.webhook_url, json=payload, timeout=self.alert_conf.timeout_seconds)
            response.raise_for_status()
            logger.info(f"Alert sent to {self.default_channel}. Severity: {severity}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send alert via webhook: {e.__class__.__name__}. Check URL/Token/Timeout.")
            return False

    async def async_send_alert(self, message: str, severity: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Triển khai phương thức Contract: Gửi cảnh báo bất đồng bộ bằng cách chạy logic đồng bộ trên executor.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._send_alert_sync,
            message,
            severity,
            context
        )