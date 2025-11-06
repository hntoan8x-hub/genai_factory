# src/shared_libs/monitoring/contracts/base_alert_adapter.py

import abc
from typing import Optional, Any, Dict

class BaseAlertAdapter(abc.ABC):
    """
    Abstract Base Class (Contract) cho mọi hệ thống gửi cảnh báo (Slack, PagerDuty, Teams).
    """

    @abc.abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Khởi tạo adapter với cấu hình đã được xác thực (AlertConfigSchema).
        """
        self.config = config
        pass

    @abc.abstractmethod
    async def async_send_alert(self, message: str, severity: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Gửi cảnh báo bất đồng bộ đến hệ thống được cấu hình.

        Args:
            message (str): Nội dung cảnh báo chính.
            severity (str): Mức độ nghiêm trọng (CRITICAL, WARNING, INFO).
            context (Dict): Dữ liệu bổ sung (request_id, model_version, v.v.).
            
        Returns:
            bool: True nếu cảnh báo được gửi thành công.
        """
        raise NotImplementedError