# src/shared_libs/validation/contracts/base_performance_client.py
# -*- coding: utf-8 -*-

import abc
from typing import Dict, Any

class BasePerformanceClient(abc.ABC):
    """
    Abstract Base Class (Contract) cho mọi công cụ kiểm tra tải (Load Testing Clients).

    Đảm bảo mọi client đều có thể chạy và trả về bộ metrics chuẩn.
    """

    @abc.abstractmethod
    def __init__(self, endpoint_url: str, config: Dict[str, Any]):
        """Khởi tạo client với URL endpoint và cấu hình test."""
        self.endpoint_url = endpoint_url
        self.config = config
        pass

    @abc.abstractmethod
    async def run_test(self) -> Dict[str, Any]:
        """
        Thực thi kiểm tra tải bất đồng bộ (async).

        Returns:
            Dict[str, Any]: Bộ metrics chuẩn (p95_latency_ms, error_rate, total_requests).
        """
        raise NotImplementedError