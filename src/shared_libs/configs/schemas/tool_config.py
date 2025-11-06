# shared_libs/configs/schemas/tool_config.py

from pydantic import BaseModel, Field, SecretStr, PositiveInt
from typing import List, Optional
from shared_libs.configs.schemas import ToolName # Import Enums từ __init__.py

# --- 1. BASE CONFIG SCHEMAS (REQUIRED FOR ALL TOOLS) ---
class ToolBaseConfig(BaseModel):
    """Cấu hình cơ sở cho mọi Tool. Đảm bảo mọi Tool đều có định danh và mô tả."""
    type: ToolName = Field(..., description="Loại Tool (Enum).")
    name: str = Field(..., description="Tên định danh duy nhất của Tool (ví dụ: 'financial_sql').")
    description: str = Field(..., description="Mô tả chi tiết để LLM có thể gọi Tool.")
    is_read_only: bool = Field(True, description="Chỉ định xem Tool này có thay đổi trạng thái bên ngoài không (ví dụ: SQL SELECT là True, Email SENDER là False).")
    # Các trường chung khác (ví dụ: timeout_sec: PositiveInt = 60)

# --- 2. SPECIALIZED TOOL CONFIG SCHEMAS (NGHIỆP VỤ & KẾT NỐI) ---

class SQLToolConfig(ToolBaseConfig):
    type: ToolName = ToolName.SQL_EXECUTOR
    db_connection_string: SecretStr = Field(..., description="Chuỗi kết nối DB (nên được mã hóa/lấy từ Secret Manager).")
    allowed_tables: List[str] = Field(..., description="Danh sách các bảng SQL mà Tool này được phép truy vấn.")

class EmailToolConfig(ToolBaseConfig):
    type: ToolName = ToolName.EMAIL_SENDER
    smtp_server: str = Field(..., description="Máy chủ SMTP.")
    sender_email: str = Field(..., description="Địa chỉ email người gửi.")
    password_secret_name: str = Field(..., description="Tên secret chứa mật khẩu SMTP.")
    port: PositiveInt = Field(587, description="Cổng SMTP.")

class SlackToolConfig(ToolBaseConfig):
    type: ToolName = ToolName.SLACK_NOTIFIER
    slack_webhook_url: SecretStr = Field(..., description="URL webhook Slack để gửi thông báo.")
    default_channel: str = Field("alerts-mlops", description="Kênh mặc định để gửi thông báo.")

class DocumentRetrieverConfig(ToolBaseConfig):
    type: ToolName = ToolName.DOCUMENT_RETRIEVER
    vector_db_config_key: str = Field(..., description="Key cấu hình để kết nối tới Vector Database.")
    default_collection: str = Field(..., description="Bộ sưu tập Vector DB mặc định để tìm kiếm.")

class DataAPIToolConfig(ToolBaseConfig):
    type: ToolName = ToolName.DATA_API_CONNECTOR
    base_url: str = Field(..., description="URL cơ sở của API.")
    auth_token_secret_name: Optional[str] = Field(None, description="Tên secret chứa Auth Token nếu cần.")

# --- 3. GOVERNANCE/UTILITY TOOL CONFIG SCHEMAS (Cần cho Tool Coordinator) ---

class AuditToolConfig(ToolBaseConfig):
    type: ToolName = ToolName.AUDIT_TOOL
    log_sink_uri: str = Field(..., description="URI của dịch vụ ghi nhật ký tập trung (ví dụ: ELK stack endpoint).")
    is_read_only: bool = Field(False, description="Audit Tool ghi dữ liệu.")

class CacheToolConfig(ToolBaseConfig):
    type: ToolName = ToolName.CACHE_TOOL
    redis_connection_string: str = Field(..., description="Chuỗi kết nối Redis/Memcached.")
    default_ttl_seconds: PositiveInt = Field(3600, description="Thời gian sống mặc định của Cache.")
    is_read_only: bool = Field(False, description="Cache Tool vừa đọc vừa ghi dữ liệu.")