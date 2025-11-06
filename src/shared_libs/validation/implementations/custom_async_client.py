# src/shared_libs/validation/implementations/custom_async_client.py (Đổi tên file cho rõ ràng)

import asyncio
import time
import random
from typing import Dict, Any, List, Optional
import httpx # Thư viện HTTP client bất đồng bộ thực tế

from shared_libs.testing.contracts.base_performance_client import BasePerformanceClient
# Giả định đã import LoadTestConfigSchema từ bước tiếp theo
from shared_libs.testing.configs.load_test_schema import LoadTestConfigSchema 

class CustomAsyncPerformanceClient(BasePerformanceClient):
    """
    Adapter Client sử dụng httpx và asyncio để tạo tải thực tế.
    """

    def __init__(self, endpoint_url: str, config: Dict[str, Any]):
        super().__init__(endpoint_url, config)
        
        # Hardening 1: Lấy các tham số từ config (đã được validate)
        self.test_config = LoadTestConfigSchema(**config) # Khởi tạo từ Schema
        self.target_qps = config.get('target_qps', 1) 
        self.duration_seconds = config.get('duration_seconds', 10)
        self.num_concurrent_tasks = config.get('num_concurrent_tasks', 10) # Số worker đồng thời
        
        # Thêm MOCK cho Prompt/Payload (sẽ được Hardening sau)
        self.mock_payload = {"prompt": "What is the capital of France?", "max_tokens": 100}
        
        # State
        self.total_requests = 0
        self.total_errors = 0
        self.latencies: List[float] = []
        self.client: Optional[httpx.AsyncClient] = None


    async def _send_request(self) -> float:
        """Thực hiện một request API bất đồng bộ và ghi lại độ trễ."""
        self.total_requests += 1
        start_time = time.perf_counter()
        
        try:
            # Hardening 2: THỰC HIỆN HTTP CALL BẤT ĐỒNG BỘ
            # Giả định Endpoint phản hồi 200/400 (Client Errors)
            response = await self.client.post(
                self.endpoint_url, 
                json=self.mock_payload,
                timeout=5.0 # Thêm timeout cho từng request
            )
            
            # Kiểm tra trạng thái HTTP (Hardening)
            if response.status_code >= 500:
                self.total_errors += 1
                return -1.0 # Báo lỗi 5xx
            
            # Giả định nếu trạng thái < 500 là thành công
            end_time = time.perf_counter()
            return (end_time - start_time) # Trả về tổng độ trễ

        except httpx.TimeoutException:
            self.total_errors += 1
            logger.warning(f"Request timed out for URL: {self.endpoint_url}")
            return -1.0
        except Exception as e:
            self.total_errors += 1
            logger.error(f"Critical error sending request: {e}")
            return -1.0 


    async def _worker_loop(self):
        """Worker gửi request với QPS đã định (Dùng Rate Limiting Token Bucket)."""
        
        # Worker sử dụng Pacing dựa trên QPS mục tiêu (Nếu có nhiều worker, QPS này là tổng)
        requests_per_second_per_worker = self.target_qps / self.num_concurrent_tasks
        time_per_request = 1.0 / requests_per_second_per_worker
        
        while time.perf_counter() < self.end_time:
            start_time = time.perf_counter()
            
            # Hardening 3: Gọi hàm gửi request thực tế
            latency = await self._send_request()
            
            if latency >= 0:
                self.latencies.append(latency)
            
            # Điều chỉnh thời gian chờ để đạt QPS mục tiêu
            elapsed = time.perf_counter() - start_time
            sleep_time = time_per_request - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    def _calculate_p95(self) -> int:
        """Tính toán độ trễ P95 (percentile 95)."""
        if len(self.latencies) < 100: # Cần số lượng mẫu đủ lớn để tính P95 tin cậy
            return 0 
        
        sorted_latencies = sorted(self.latencies)
        index = int(0.95 * len(sorted_latencies))
        p95_seconds = sorted_latencies[index if index < len(sorted_latencies) else -1]
        return int(p95_seconds * 1000) # Trả về mili giây (ms)

    async def run_test(self) -> Dict[str, Any]:
        """Chạy kiểm tra tải và trả về kết quả."""
        self.start_time = time.perf_counter()
        self.end_time = self.start_time + self.duration_seconds
        
        # Hardening 4: Khởi tạo httpx client cho session
        async with httpx.AsyncClient() as client:
            self.client = client
            
            # Chạy nhiều worker đồng thời
            workers = [self._worker_loop() for _ in range(self.num_concurrent_tasks)]
            
            # Giới hạn tổng thời gian chạy
            try:
                 await asyncio.gather(*workers, return_exceptions=True)
            except Exception:
                 pass 

        actual_duration = time.perf_counter() - self.start_time
        
        return {
            'total_requests': self.total_requests,
            'total_errors': self.total_errors,
            'actual_qps': self.total_requests / actual_duration,
            'p95_latency_ms': self._calculate_p95(),
            'error_rate': self.total_errors / self.total_requests if self.total_requests > 0 else 0.0
        }