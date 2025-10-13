# shared_libs/factory/llm_factory.py

from shared_libs.base.base_llm import BaseLLM
from shared_libs.atomic.llms.openai_llm import OpenAILLM 
from shared_libs.atomic.llms.huggingface_llm import HuggingFaceLLM 
from typing import Dict, Any

MODEL_MAP = {
    "openai": OpenAILLM,
    "huggingface": HuggingFaceLLM,
    # Add AnthropicLLM, etc.
}

class LLMFactory:
    
    @staticmethod
    def create_llm(llm_config: Dict[str, Any]) -> BaseLLM:
        """
        Instantiates the primary LLM and configures the fallback mechanism.
        """
        
        # 1. Instantiate Primary LLM
        primary_conf = llm_config.get("primary", {})
        primary_type = primary_conf.get("type")
            
        PrimaryLLMClass = MODEL_MAP.get(primary_type)
        if not PrimaryLLMClass:
            raise ValueError(f"LLM type '{primary_type}' not supported in Factory.")
            
        primary_llm = PrimaryLLMClass(primary_conf.get("config", {}))
        
        # 2. Configure Fallback LLM (HARDENING INTEGRATION)
        fallback_conf = llm_config.get("fallback")
        if fallback_conf:
            fallback_type = fallback_conf.get("type")
            FallbackLLMClass = MODEL_MAP.get(fallback_type)
            
            if not FallbackLLMClass:
                print(f"Warning: Fallback LLM type '{fallback_type}' not configured properly.")
            else:
                fallback_llm = FallbackLLMClass(fallback_conf.get("config", {}), is_fallback=True)
                # Link the fallback model to the primary wrapper
                primary_llm.set_fallback_llm(fallback_llm)

        return primary_llm