# src/shared_libs/monitoring/healthcheck.py (FINAL PRODUCTION CODE)

import asyncio
import logging
from typing import Dict, Any, List, Type, Optional
from prometheus_client import Gauge, Info # Import Prometheus
# Import Contract
from shared_libs.monitoring.contracts.base_health_checker import BaseHealthStatus, BaseHealthChecker 
# Import các Checker con (ví dụ)
from shared_libs.monitoring.healthcheckers.llm_checker import LLMHealthChecker 

logger = logging.getLogger(__name__)

# --- METRICS DEFINITION (PROMETHEUS HARDENING) ---
# Gauge: 1 = OK, 0 = UNHEALTHY (Dùng cho Alertmanager)
HEALTH_GAUGE = Gauge(
    'genai_dependency_health_status', 
    'Health status of a service dependency (1=ok, 0=unhealthy)', 
    labelnames=['dependency_name', 'service_type']
)

# Info: Ghi lại phiên bản/thông tin của Service
SERVICE_INFO = Info(
    'genai_assistant_info', 
    'Information about the GenAI Assistant service and its version.'
)
SERVICE_INFO.info({'version': 'v1.4', 'env': 'prod'}) # MOCK: Ghi thông tin Service

class HealthCheckerOrchestrator:
    """
    Orchestrates and runs health checks on all registered dependencies asynchronously.
    """

    def __init__(self, checker_configs: Dict[str, Dict[str, Any]]):
        """
        Initializes the health checker with its dependency configurations.
        """
        self.checkers: Dict[str, BaseHealthChecker] = {}
        
        # Hardening 1: Khởi tạo các Checker con dựa trên cấu hình
        for name, config in checker_configs.items():
            # Hardening: Sử dụng Factory hoặc Registry để chọn Checker
            checker_class = self._get_checker_class(name) # Ví dụ: LLMHealthChecker
            if checker_class:
                self.checkers[name] = checker_class(name, config)
            else:
                 logger.warning(f"No specific checker found for dependency: {name}")

    def _get_checker_class(self, name: str) -> Optional[Type[BaseHealthChecker]]:
        """MOCK: Registry đơn giản để ánh xạ tên Dependency sang Checker Class."""
        registry = {
            "llm_service": LLMHealthChecker,
            "vector_db": None, # Chưa implement
            "mlops_db": None,
        }
        return registry.get(name)

    async def async_run_all_checks(self) -> Dict[str, Any]:
        """
        Runs health checks on all registered services asynchronously.
        """
        if not self.checkers:
            return {"status": "ok", "message": "No checkers registered."}

        tasks = [checker.async_check_health() for checker in self.checkers.values()]
        results: List[Dict[str, Any]] = await asyncio.gather(*tasks, return_exceptions=True)
        
        report = {"status": "ok", "checks": {}}
        
        # Hardening 2: Xử lý kết quả và ghi Metrics
        for name, result in zip(self.checkers.keys(), results):
            
            check_status: BaseHealthStatus = "unhealthy"
            
            if isinstance(result, Exception):
                # Bắt lỗi Exception nếu checker thất bại hoàn toàn
                check_status = "unhealthy"
                report["checks"][name] = {"status": check_status, "error": str(result)}
            else:
                check_status = result.get("status", "unhealthy") # Lấy status từ Checker con
                report["checks"][name] = result
            
            # Ghi Metrics cho Prometheus (CRITICAL OBSERVABILITY)
            metric_value = 1 if check_status == "ok" else 0
            HEALTH_GAUGE.labels(dependency_name=name, service_type=name).set(metric_value)
            
            if check_status == "unhealthy":
                report["status"] = "unhealthy"
                logger.critical(f"HEALTH CHECK FAILED: Dependency {name} is UNHEALTHY.")
            elif check_status == "degraded" and report["status"] == "ok":
                report["status"] = "degraded" # Nếu có degrade, tổng thể là degrade

        logger.info(f"Overall Health Status: {report['status'].upper()}")
        return report