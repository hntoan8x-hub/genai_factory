# src/shared_libs/monitoring/contracts/base_evaluation_reporter.py

import abc
from typing import Dict, Any, Optional

class BaseEvaluationReporter(abc.ABC):
    """
    Abstract Base Class (Contract) cho các lớp lưu trữ và báo cáo kết quả đánh giá mô hình.
    """

    @abc.abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Khởi tạo reporter với cấu hình lưu trữ đã được xác thực (ReporterStorageSchema).
        """
        self.config = config
        pass

    @abc.abstractmethod
    def format_report(self, 
                      request_id: str, 
                      model_version: str, 
                      eval_results: Dict[str, Any],
                      timestamp: float) -> Dict[str, Any]:
        """
        Định dạng kết quả đánh giá thô thành cấu trúc dữ liệu phẳng (flat structure)
        chuẩn để lưu trữ hoặc hiển thị.

        Args:
            request_id (str): ID duy nhất của phiên chạy đánh giá.
            model_version (str): Tag/phiên bản của mô hình được đánh giá.
            eval_results (Dict): Kết quả đánh giá thô từ Evaluation Orchestrator.
            timestamp (float): Thời gian epoch của phiên chạy.

        Returns:
            Dict[str, Any]: Báo cáo đã được định dạng và làm phẳng.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def async_store_report(self, report_data: Dict[str, Any]) -> None:
        """
        Lưu trữ báo cáo đã được định dạng vào Persistent Storage (DB, MLflow, S3).
        """
        raise NotImplementedError