# shared_libs/configs/schemas/evaluator_config.py

from pydantic import BaseModel, Field, PositiveInt
from typing import Dict, Any, List, Optional
from shared_libs.configs.schemas import LLMType # Cần cho việc chỉ định LLM dùng để đánh giá

# --- BASE CONFIG SCHEMAS ---

class EvaluatorBaseConfig(BaseModel):
    """Cấu hình cơ sở cho mọi Evaluator."""
    type: str = Field(..., description="Loại Evaluator (ví dụ: 'toxicity', 'hallucination').")
    llm_config_key: Optional[str] = Field(None, description="Key LLM nếu Evaluator cần LLM để đánh giá (ví dụ: Hallucination).")
    threshold: float = Field(0.8, ge=0.0, le=1.0, description="Ngưỡng điểm để đánh giá PASS/FAIL.")
    
class ToxicityEvaluatorConfig(EvaluatorBaseConfig):
    type: str = Field('toxicity')
    # Giả định Evaluator này dùng API bên ngoài (ví dụ: Perspective API)
    api_key_secret: Optional[str] = Field(None, description="Tên secret chứa API key của dịch vụ Toxicity.")

class HallucinationEvaluatorConfig(EvaluatorBaseConfig):
    type: str = Field('hallucination')
    # Bắt buộc phải dùng LLM để so sánh
    llm_config_key: str = Field(..., description="Key LLM được sử dụng để so sánh độ chính xác.")
    ground_truth_key: str = Field("source_documents", description="Key trong context chứa dữ liệu nguồn để so sánh.")
    
class ComplianceEvaluatorConfig(EvaluatorBaseConfig):
    type: str = Field('compliance_check')
    policy_id: str = Field(..., description="ID của chính sách nội bộ được sử dụng làm quy tắc kiểm tra.")
    
class EvaluatorEntry(BaseModel):
    """Mô tả một công cụ đánh giá được áp dụng trong một Pipeline cụ thể."""
    type: str = Field(..., description="Loại Evaluator.")
    enabled: bool = Field(True, description="Được bật/tắt.")
    config: Dict[str, Any] = Field(default_factory=dict, description="Các tham số khởi tạo chuyên biệt cho Evaluator.")

class EvaluatorConfigSchema(BaseModel):
    """Schema chính chứa danh sách các Evaluator được áp dụng cho một Pipeline."""
    evaluators: List[EvaluatorEntry] = Field(..., description="Danh sách các công cụ đánh giá được kích hoạt.")


# --- REGISTRY MAP (Sử dụng bởi SchemaRegistry) ---
EVALUATOR_CONFIG_MAP: Dict[str, type[BaseModel]] = {
    "toxicity": ToxicityEvaluatorConfig,
    "hallucination": HallucinationEvaluatorConfig,
    "compliance_check": ComplianceEvaluatorConfig,
    "schema": EvaluatorConfigSchema,
}