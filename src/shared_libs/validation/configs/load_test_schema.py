# src/shared_libs/validation/configs/load_test_schema.py

# Cần cài đặt: pip install pydantic
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, conint, confloat, conlist, HttpUrl

class LoadTestConfigSchema(BaseModel):
    """
    Schema cấu hình kiểm thử tải cho GenAI Assistant Endpoint.
    """
    
    # ----------------- A. Load Configuration -----------------
    
    target_qps: conint(gt=0) = Field(..., description="Tần suất request mục tiêu (QPS) tổng cộng.")
    duration_seconds: conint(gt=0) = Field(30, description="Tổng thời gian chạy test (giây).")
    num_concurrent_tasks: conint(ge=1) = Field(10, description="Số lượng tác vụ (Worker) chạy đồng thời để tạo tải.")
    
    # ----------------- B. Quality Gate (SLA Thresholds) -----------------
    
    max_p95_latency_ms: conint(gt=0) = Field(500, description="Ngưỡng độ trễ P95 tối đa cho phép (mili giây).")
    max_error_rate: confloat(ge=0, le=1) = Field(0.01, description="Ngưỡng tỷ lệ lỗi tối đa cho phép (0.0 - 1.0).")
    
    # ----------------- C. Input Data (Hardening) -----------------
    
    # Giả định tải các mẫu Input Prompt từ một nguồn dữ liệu
    input_data_uri: Optional[HttpUrl] = Field(None, description="URI đến kho chứa các mẫu prompt đầu vào thực tế (ví dụ: S3/GCS URL).")
    mock_payload: Dict[str, Any] = Field(
        default_factory=lambda: {"prompt": "Tell me a joke.", "max_tokens": 100},
        description="Payload mặc định nếu không có dữ liệu input thực tế."
    )
    
    # ----------------- D. Endpoint Configuration -----------------
    
    # Timeout cho một request riêng lẻ (để tránh request bị treo)
    request_timeout_seconds: confloat(gt=0) = Field(5.0, description="Timeout tối đa cho mỗi HTTP request đơn lẻ (giây).")