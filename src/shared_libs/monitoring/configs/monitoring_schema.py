# src/shared_libs/monitoring/configs/monitoring_schema.py

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, conint, confloat, HttpUrl

# -----------------------------------------------------
# 1. Alerting Schema (for simple_alert_adapter.py)
# -----------------------------------------------------

class AlertConfigSchema(BaseModel):
    """
    Schema cấu hình cho hệ thống gửi cảnh báo (Slack, PagerDuty, v.v.).
    """
    # CRITICAL: Webhook URL phải được xác thực là URL hợp lệ
    webhook_url: HttpUrl = Field(..., description="URL Webhook của hệ thống cảnh báo (Slack/PagerDuty).")
    default_channel: str = Field(..., description="Kênh mặc định để gửi cảnh báo.")
    
    # Hardening: Giới hạn tài nguyên/thời gian
    timeout_seconds: confloat(gt=0) = Field(5.0, description="Timeout cho synchronous HTTP request gửi cảnh báo.")
    max_workers: conint(ge=1) = Field(1, description="Số lượng worker tối đa cho ThreadPoolExecutor.")
    
# -----------------------------------------------------
# 2. Cost Monitor Schema (for cost_monitor.py)
# -----------------------------------------------------

class CostMonitorConfigSchema(BaseModel):
    """
    Schema cấu hình theo dõi chi phí và ngưỡng cảnh báo.
    """
    # Hardening: Ngưỡng chi phí
    cost_threshold_usd: confloat(gt=0) = Field(100.0, description="Ngưỡng chi phí tích lũy hàng ngày (USD) để kích hoạt cảnh báo.")
    
    # Hardening: Ánh xạ giá token
    token_pricing_map: Dict[str, confloat(ge=0)] = Field(
        ..., 
        description="Ánh xạ tên model (ví dụ: gpt-4o) sang giá mỗi token (USD)."
    )
    
# -----------------------------------------------------
# 3. Evaluation Reporter Schema (for evaluation_reporter.py)
# -----------------------------------------------------

class ReporterStorageSchema(BaseModel):
    """
    Schema cấu hình lưu trữ kết quả đánh giá mô hình.
    """
    # Hardening: Giới hạn loại storage
    storage_type: Literal["mlflow", "database", "s3", "none"] = Field(..., description="Loại backend storage để lưu báo cáo.")
    
    # Thông số cấu hình tùy chọn
    tracking_uri: Optional[str] = Field(None, description="MLflow tracking URI (nếu storage_type='mlflow').")
    db_connection_string: Optional[str] = Field(None, description="Connection string cho MLOps Database (nếu storage_type='database').")
    table_name: Optional[str] = Field(None, description="Tên bảng/entity để lưu dữ liệu.")
    

# -----------------------------------------------------
# 4. Global Monitoring Config (Tập hợp)
# -----------------------------------------------------

class MonitoringConfigSchema(BaseModel):
    """
    Schema tổng hợp cho toàn bộ layer Monitoring.
    """
    alerting: AlertConfigSchema
    cost_monitoring: CostMonitorConfigSchema
    evaluation_reporting: ReporterStorageSchema