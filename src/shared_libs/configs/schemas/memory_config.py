# shared_libs/configs/schemas/memory_config.py

from pydantic import BaseModel, Field, SecretStr, PositiveInt
from typing import Dict, Any, Optional
from shared_libs.configs.schemas import LLMType

# --- BASE CONFIG SCHEMAS ---

class MemoryBaseConfig(BaseModel):
    """Cấu hình cơ sở cho mọi hệ thống Memory (Redis, SQL, v.v.)."""
    type: str = Field(..., description="Loại Memory (ví dụ: 'redis', 'dynamo').")
    session_timeout_sec: PositiveInt = Field(3600, description="Thời gian sống (TTL) của session context.")
    max_context_length: PositiveInt = Field(8192, description="Giới hạn kích thước context (tokens/bytes) để tránh quá tải.")
    
class RedisMemoryConfig(MemoryBaseConfig):
    type: str = Field('redis')
    connection_string: SecretStr = Field(..., description="Chuỗi kết nối Redis (nên được lấy từ Secret Manager).")
    ssl_enabled: bool = Field(True, description="Bật SSL/TLS cho kết nối.")
    
class SQLMemoryConfig(MemoryBaseConfig):
    type: str = Field('sql_db')
    db_connection_string: SecretStr = Field(..., description="Chuỗi kết nối cơ sở dữ liệu SQL.")
    table_name: str = Field("agent_sessions", description="Tên bảng lưu trữ session.")


# --- REGISTRY MAP (Sử dụng bởi SchemaRegistry) ---
MEMORY_CONFIG_MAP: Dict[str, type[BaseModel]] = {
    "redis": RedisMemoryConfig,
    "sql_db": SQLMemoryConfig,
}