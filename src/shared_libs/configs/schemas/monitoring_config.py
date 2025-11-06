# shared_libs/configs/schemas/monitoring_config.py

from pydantic import BaseModel, Field, SecretStr, PositiveInt
from typing import Dict, Any, List, Optional
from shared_libs.configs.schemas import LLMType # Import Enums

# --- 1. ALERT CONFIG SCHEMAS (REQUIRED FOR ALL ALERTING LOGIC) ---

class AlertAdapterConfig(BaseModel):
    """Cấu hình cho SimpleAlertAdapter (Gửi cảnh báo ra bên ngoài)."""
    type: str = Field('slack_webhook', description="Loại dịch vụ cảnh báo.")
    webhook_url: SecretStr = Field(..., description="URL webhook bí mật để gửi cảnh báo.")
    default_channel: str = Field(..., description="Kênh/Đích gửi mặc định.")
    max_workers: PositiveInt = Field(1, description="Số lượng worker tối đa cho ThreadPoolExecutor.")

# --- 2. MONITOR CONFIG SCHEMAS (HARDENING: FinOps & Thresholds) ---

class CostMonitorConfig(BaseModel):
    """Cấu hình cho CostMonitor (Kiểm soát Chi phí)."""
    cost_threshold_usd: float = Field(100.0, ge=0.0, description="Ngưỡng chi phí hàng ngày (USD) để kích hoạt cảnh báo.")
    alert_adapter_key: str = Field(..., description="Key mapping đến AlertAdapter instance để gửi cảnh báo.")
    # Có thể thêm pricing_model_config nếu cần cấu hình chi tiết hơn

class LatencyMonitorConfig(BaseModel):
    """Cấu hình cho LatencyMonitor (Không có tham số phức tạp, chủ yếu là định danh)."""
    # Không cần field bắt buộc, nhưng giúp đăng ký trong Factory
    metric_namespace: str = Field("genai_service", description="Namespace Prometheus cho Latency.")
    
# --- 3. LOGGING/AUDIT CONFIG SCHEMAS (HARDENING: Compliance) ---

class AuditLoggerConfig(BaseModel):
    """Cấu hình cho AuditLogger (Ghi nhật ký Tuân thủ)."""
    log_sink_uri: str = Field(..., description="URI của dịch vụ ghi nhật ký tập trung (ví dụ: ELK endpoint).")
    alert_adapter_key: str = Field(..., description="Key mapping đến AlertAdapter instance cho sự kiện bảo mật.")
    
# --- 4. HEALTHCHECK CONFIG SCHEMAS (HARDENING: System Management) ---

class HealthCheckConfig(BaseModel):
    """Cấu hình cho HealthChecker."""
    dependencies_to_check: List[str] = Field(..., description="Danh sách các tên service cần kiểm tra.")
    check_timeout_sec: PositiveInt = Field(5, description="Giới hạn thời gian (giây) cho mỗi kiểm tra.")

# --- REGISTRY MAP (Sử dụng bởi SchemaRegistry) ---
MONITORING_CONFIG_MAP: Dict[str, type[BaseModel]] = {
    "alert_adapter": AlertAdapterConfig,
    "cost_monitor": CostMonitorConfig,
    "audit_logger": AuditLoggerConfig,
    "health_checker": HealthCheckConfig,
}