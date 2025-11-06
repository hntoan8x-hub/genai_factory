# src/shared_libs/monitoring/contracts/base_health_checker.py

import abc
from typing import Dict, Any, Literal

# Định nghĩa kiểu trả về chuẩn cho mỗi Health Check
HealthStatus = Literal["ok", "degraded", "unhealthy"]

class BaseHealthChecker(abc.ABC):
    """
    Contract cho các lớp kiểm tra sức khỏe của một Dependency cụ thể.
    """

    @abc.abstractmethod
    def __init__(self, dependency_name: str, config: Dict[str, Any]):
        """Khởi tạo checker với tên Dependency và cấu hình."""
        self.dependency_name = dependency_name
        self.config = config
        pass

    @abc.abstractmethod
    async def async_check_health(self) -> Dict[str, Any]:
        """
        Thực hiện kiểm tra sức khỏe bất đồng bộ.
        
        Returns:
            Dict[str, Any]: Phải chứa khóa 'status' (HealthStatus) và có thể chứa 'details'.
                            Ví dụ: {"status": "ok", "latency_ms": 50}
        """
        raise NotImplementedError