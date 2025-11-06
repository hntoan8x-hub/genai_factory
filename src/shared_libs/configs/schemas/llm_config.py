# shared_libs/configs/schemas/llm_config.py

from pydantic import BaseModel, Field, SecretStr, PositiveInt
from typing import Optional, Union, Dict
from shared_libs.configs.schemas import LLMType # Import Enum từ __init__.py
from pathlib import Path

# --- BASE CONFIG SCHEMAS (REQUIRED FOR ALL LLMs) ---

class LLMBaseConfig(BaseModel):
    """Cấu hình cơ sở cho mọi LLM (OpenAI, Anthropic, HuggingFace, v.v.)."""
    type: LLMType = Field(..., description="Loại mô hình LLM (Enum).")
    model_name: str = Field(..., description="Tên mô hình cụ thể (ví dụ: gpt-4o, claude-3).")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Tham số nhiệt độ.")
    max_tokens: Optional[PositiveInt] = Field(None, description="Giới hạn token đầu ra.")

class OpenAILLMConfig(LLMBaseConfig):
    type: LLMType = LLMType.OPENAI
    api_key: SecretStr = Field(..., description="Khóa API (nên được mã hóa/lấy từ Secret Manager).")
    org_id: Optional[str] = Field(None, description="Organization ID nếu cần thiết.")

class HuggingFaceLLMConfig(LLMBaseConfig):
    type: LLMType = LLMType.HUGGINGFACE
    model_path: Path = Field(..., description="Đường dẫn cục bộ hoặc URI tới mô hình.")
    device: str = Field("auto", description="Thiết bị sử dụng (e.g., 'cuda', 'cpu', 'auto').")
    auth_token: Optional[SecretStr] = Field(None, description="HuggingFace Hub Access Token.")


class LLMServiceConfig(BaseModel):
    """Schema chính để khởi tạo LLMWrapper (Quản lý Primary & Fallback)."""
    primary: OpenAILLMConfig = Field(..., description="Cấu hình LLM chính (Primary).")
    fallback: Optional[Union[OpenAILLMConfig, HuggingFaceLLMConfig]] = Field(
        None, description="Cấu hình LLM dự phòng (Fallback) nếu Primary thất bại."
    )
    timeout: PositiveInt = Field(60, description="Giới hạn thời gian (giây) cho mỗi cuộc gọi LLM.")
    retry_attempts: PositiveInt = Field(3, description="Số lần thử lại tối đa trước khi chuyển sang Fallback.")


# --- REGISTRY MAP (Sử dụng bởi SchemaRegistry) ---
LLM_CONFIG_MAP: Dict[str, type[BaseModel]] = {
    "openai": OpenAILLMConfig,
    "huggingface": HuggingFaceLLMConfig,
    "service_config": LLMServiceConfig,
}