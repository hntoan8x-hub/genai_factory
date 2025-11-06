# shared_libs/configs/schemas/utility_config.py

from pydantic import BaseModel, Field, SecretStr, PositiveInt
from typing import Dict, Any, List, Optional, Union
from shared_libs.configs.schemas import LLMType # Giả định LLMType đã được định nghĩa trong __init__.py
from pathlib import Path


# --- 1. LLM CONFIG SCHEMAS (HARDENING: Resilience) ---
class LLMBaseConfig(BaseModel):
    """Cấu hình cơ sở cho mọi LLM (OpenAI, Anthropic, HuggingFace, v.v.)."""
    type: LLMType = Field(..., description="Loại mô hình LLM (Enum).")
    model_name: str = Field(..., description="Tên mô hình cụ thể (ví dụ: gpt-4o, claude-3).")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Tham số nhiệt độ.")
    max_tokens: Optional[PositiveInt] = Field(None, description="Giới hạn token đầu ra.")

class OpenAILLMConfig(LLMBaseConfig):
    type: LLMType = LLMType.OPENAI
    api_key: SecretStr = Field(..., description="Khóa API (nên được lấy từ Secret Manager).")

class HuggingFaceLLMConfig(LLMBaseConfig):
    type: LLMType = LLMType.HUGGINGFACE
    model_path: Path = Field(..., description="Đường dẫn cục bộ hoặc URI tới mô hình.")


class LLMServiceConfig(BaseModel):
    """Schema chính để khởi tạo LLMWrapper (Quản lý Primary & Fallback)."""
    primary: OpenAILLMConfig = Field(..., description="Cấu hình LLM chính.")
    fallback: Optional[Union[OpenAILLMConfig, HuggingFaceLLMConfig]] = Field(
        None, description="Cấu hình LLM dự phòng (fallback) nếu Primary thất bại."
    )
    timeout: PositiveInt = Field(30, description="Giới hạn thời gian (giây) cho mỗi cuộc gọi LLM.")


# --- 2. EVALUATOR CONFIG SCHEMAS (HARDENING: Quality Assurance) ---
class EvaluatorEntry(BaseModel):
    """Mô tả một công cụ đánh giá (ví dụ: Safety, Hallucination, Compliance)."""
    type: str = Field(..., description="Loại Evaluator (ví dụ: 'safety_check', 'hallucination_score').")
    enabled: bool = Field(True, description="Được bật/tắt.")
    context: Dict[str, Any] = Field(default_factory=dict, description="Tham số tùy chỉnh cho Evaluator.")

class EvaluatorConfigSchema(BaseModel):
    """Schema chính chứa danh sách các Evaluator được áp dụng cho một Pipeline."""
    evaluators: List[EvaluatorEntry] = Field(..., description="Danh sách các công cụ đánh giá được kích hoạt.")


# --- 3. PROMPT CONFIG SCHEMAS (HARDENING: Validation & Versioning) ---
class PromptBaseConfig(BaseModel):
    """Cấu hình cơ sở cho mọi Prompt Template."""
    type: str = Field(..., description="Loại Prompt (ví dụ: 'react', 'supervisor_decision').")
    version: str = Field("v1.0", description="Phiên bản của Prompt Template.")
    template: str = Field(..., description="Chuỗi Template gốc của Prompt.")
    variables: List[str] = Field(..., description="Danh sách các biến cần được điền vào template.")
    
class RAGPromptConfig(PromptBaseConfig):
    """Cấu hình cho các Prompt chuyên biệt về RAG (chú thích nguồn)."""
    source_citation_format: str = Field("[{index}] {source_id}", description="Định dạng trích dẫn nguồn.")