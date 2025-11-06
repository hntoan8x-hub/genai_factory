# src/shared_libs/logging/configs/audit_schema.py

from typing import Dict, Any, Literal, Optional
from pydantic import BaseModel, Field, conint, confloat, HttpUrl

class AuditConfigSchema(BaseModel):
    """
    Schema cấu hình cho Audit Logger.
    """
    # MOCK: Thiết lập các endpoint/storage cho Audit Log
    log_storage_uri: Optional[str] = Field(None, description="URI lưu trữ Audit Log (ví dụ: S3, Kafka topic).")
    compliance_level: Literal["BASIC", "STRICT", "FULL"] = Field("STRICT", description="Mức độ tuân thủ yêu cầu ghi log.")
    
# Thêm Schema cho các loại sự kiện nếu cần strict validation
class BaseAuditEventSchema(BaseModel):
    request_id: str
    user_id: str
    severity: Literal["CRITICAL", "HIGH", "WARNING", "INFO"] = "INFO"