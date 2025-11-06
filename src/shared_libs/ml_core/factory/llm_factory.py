# shared_libs/factory/llm_factory.py (FINAL HARDENED VERSION - Cập nhật)

from shared_libs.base.base_llm import BaseLLM
from shared_libs.atomic.llms.openai_llm import OpenAILLM 
from shared_libs.atomic.llms.huggingface_llm import HuggingFaceLLM 
from typing import Dict, Any, Type
# HARDENING: Import các Schema đã được chứng nhận từ cấu trúc mới
from shared_libs.configs.schemas import LLMServiceConfig, OpenAILLMConfig, HuggingFaceLLMConfig, LLMBaseConfig

# Mapping: Ánh xạ loại LLM (type string) sang lớp triển khai (class)
MODEL_MAP: Dict[str, Type[BaseLLM]] = {
    "openai": OpenAILLM,
    "huggingface": HuggingFaceLLM,
    # Thêm AnthropicLLM, v.v.
}

class LLMFactory:
    
    @staticmethod
    def _instantiate_single_llm(config: LLMBaseConfig, is_fallback: bool = False) -> BaseLLM:
        """Helper khởi tạo một LLM đơn lẻ từ cấu hình Base."""
        llm_type = config.type.value
        LLMClass = MODEL_MAP.get(llm_type)
        if not LLMClass:
            raise ValueError(f"LLM type '{llm_type}' not supported in Factory.")
        
        # Sử dụng model_dump() để lấy tất cả tham số (bao gồm cả SecretStr đã giải mã)
        return LLMClass(config.model_dump(exclude_none=True), is_fallback=is_fallback)


    @staticmethod
    def create_llm(llm_service_config: LLMServiceConfig) -> BaseLLM:
        """
        Instantiates the primary LLM and configures the fallback mechanism.
        Yêu cầu một mô hình LLMServiceConfig đã được validate.
        """
        
        # 1. Khởi tạo Primary LLM
        primary_llm = LLMFactory._instantiate_single_llm(llm_service_config.primary, is_fallback=False)
        
        # 2. Configure Fallback LLM 
        fallback_model = llm_service_config.fallback
        if fallback_model:
            try:
                fallback_llm = LLMFactory._instantiate_single_llm(fallback_model, is_fallback=True)
                primary_llm.set_fallback_llm(fallback_llm) 
            except ValueError as e:
                 print(f"Warning: Failed to configure fallback LLM: {e}")

        return primary_llm