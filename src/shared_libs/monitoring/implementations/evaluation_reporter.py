# src/shared_libs/monitoring/implementations/evaluation_reporter.py (Đổi tên file cho rõ ràng)

import json
import time # Import time (đã bị thiếu trong bản gốc)
from typing import Dict, Any, List, Optional
import logging
import asyncio

from shared_libs.monitoring.contracts.base_evaluation_reporter import BaseEvaluationReporter # Import Contract
# Import Schema đã tạo
from shared_libs.monitoring.configs.monitoring_schema import ReporterStorageSchema 

logger = logging.getLogger(__name__)

# Hardening: Triển khai Contract và sử dụng Schema
class EvaluationReporter(BaseEvaluationReporter):
    """
    Handles the standardization and formatting of Evaluation Orchestrator results
    for auditing, visualization, or persistent storage (e.g., MLOps DB).
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Hardening 1: Xác thực config bằng Schema
        self.reporter_conf = ReporterStorageSchema.model_validate(config)
        self.storage_type = self.reporter_conf.storage_type
        
        # Hardening 2: Khởi tạo Storage Connector dựa trên type
        self.storage_connector = self._initialize_storage_connector()


    def _initialize_storage_connector(self) -> Optional[Any]:
        """Helper để khởi tạo connector thực tế (DB, MLflow Adapter)."""
        if self.storage_type == "database":
            # Ví dụ: return DBAdapter(self.reporter_conf.db_connection_string)
            logger.info("Database connector initialized for reporting.")
            return True # MOCK: Trả về True nếu kết nối thành công
        elif self.storage_type == "mlflow":
            # Ví dụ: return MLflowAdapter(self.reporter_conf.tracking_uri)
            logger.info("MLflow connector initialized for reporting.")
            return True # MOCK
        else:
            logger.warning(f"Storage type '{self.storage_type}' is set. No persistent connector initialized.")
            return None


    # Hardening: Triển khai phương thức format_report (đồng bộ)
    def format_report(self, 
                      request_id: str, 
                      model_version: str, 
                      eval_results: Dict[str, Any],
                      timestamp: float) -> Dict[str, Any]:
        """
        Standardizes evaluation results into a flat format suitable for database insertion.
        """
        formatted_results = {
            "request_id": request_id,
            "model_version": model_version,
            "timestamp": timestamp, # Sử dụng timestamp truyền vào
            "overall_status": "PASS",
            "metrics": {}
        }

        for eval_name, result in eval_results.items():
            # Kiểm tra trạng thái PASS/FAIL dựa trên các Evaluator
            if result.get("status") == "FAIL" or result.get("error"):
                formatted_results["overall_status"] = "FAIL"
            
            # Trích xuất các metrics số học và làm phẳng
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, (int, float)):
                        # Hardening: Đảm bảo tên metrics rõ ràng (ví dụ: latency_p95)
                        formatted_results["metrics"][f"{eval_name}_{key}"] = value
                    # Lưu trữ các kết quả string quan trọng (ví dụ: lý do thất bại)
                    elif key == "reason" and isinstance(value, str):
                         formatted_results[f"{eval_name}_reason"] = value

        logger.debug(f"Formatted evaluation report for request {request_id}. Status: {formatted_results['overall_status']}.")
        return formatted_results

    # Hardening: Triển khai phương thức async_store_report
    async def async_store_report(self, report_data: Dict[str, Any]) -> None:
        """
        Stores the formatted evaluation report to the persistent storage connector.
        """
        if self.storage_connector:
            try:
                # Giả định storage_connector (DB/MLflow Adapter) có phương thức async_insert
                # Sử dụng tên bảng/entity từ config schema
                entity_name = self.reporter_conf.table_name if self.reporter_conf.table_name else "evaluation_runs"
                
                # MOCK: Logic gọi Connector Adapter thực tế
                # await self.storage_connector.async_insert(entity_name, report_data)
                await asyncio.sleep(0.1) # Giả lập I/O
                
                logger.info(f"Evaluation report stored successfully to {self.storage_type} for request {report_data['request_id']}.")
            except Exception as e:
                logger.error(f"Failed to store evaluation report to {self.storage_type}: {e}")
                # Có thể kích hoạt cảnh báo ở đây nếu việc lưu trữ là CRITICAL
        else:
            logger.warning("No persistent storage configured. Evaluation report stored to log only.")
            logger.debug(json.dumps(report_data))