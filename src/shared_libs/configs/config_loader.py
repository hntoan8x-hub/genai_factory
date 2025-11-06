import yaml
import os
import logging
from typing import Dict, Any, Type, Optional, Union
from pydantic import BaseModel, ValidationError

# Import all schemas directly from the registry location
# NOTE: Cần cập nhật các import này để trỏ đến các schemas Pydantic thực tế
from shared_libs.configs.global_schema_registry import ROOT_CONFIGS 
from shared_libs.feature_store.configs.feature_store_config_schema import FeatureStoreConfig 
# Giả định các schema root khác cũng được import
from shared_libs.configs.schemas.llm_config import LLMServiceConfig 
from shared_libs.configs.schemas.utility_config import RAGPromptConfig

logger = logging.getLogger(__name__)

# --- Class Registry đã được chuyển ra global_schema_registry.py ---

class ConfigLoader:
    """
    The centralized, hardened configuration loader for the GenAI Factory.
    
    It validates configurations against the schemas defined in the Global Registry.
    """
    
    def __init__(self, base_config_dir: str = "configs"):
        self._base_dir = base_config_dir
        # NOTE: Không cần _schema_registry nội bộ nữa, ta dùng ROOT_CONFIGS

    def load_yaml(self, file_path: str) -> Dict[str, Any]:
        """
        Loads a YAML file from disk (Hardening: safe_load, FileNotFoundError).
        """
        full_path = file_path
        if not os.path.isabs(file_path):
            full_path = os.path.join(self._base_dir, file_path)
            
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Configuration file not found: {full_path}")
            
        try:
            with open(full_path, 'r') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.critical(f"YAML parsing error in {full_path}: {e}")
            raise RuntimeError(f"YAML parsing failed for {full_path}")
        except Exception as e:
            logger.critical(f"Error reading configuration file {full_path}: {e}")
            raise RuntimeError(f"Configuration loading failed.")

    # -------------------------------------------------------------------
    # PUBLIC GETTERS VÀ VALIDATION (Simplified API)
    # -------------------------------------------------------------------
    
    def _validate_config_with_schema(self, raw_config: Dict[str, Any], schema_class: Type[BaseModel]) -> BaseModel:
        """Internal validation helper."""
        try:
            validated_model = schema_class.model_validate(raw_config)
            logger.debug(f"Configuration validated successfully against {schema_class.__name__}.")
            return validated_model
        except ValidationError as e:
            logger.critical(f"Configuration VALIDATION FAILED for {schema_class.__name__}: {e.errors()}", exc_info=True)
            raise RuntimeError(f"Configuration Validation Failed: {schema_class.__name__}. Errors: {e.errors()}")

    # --- Ví dụ về các Getters chuyên biệt ---

    def get_llm_service_config(self, file_path: str) -> LLMServiceConfig:
        """Loads and validates the main LLM Service Config (Primary/Fallback)."""
        raw_config = self.load_yaml(file_path)
        # LLMServiceConfig là schema root cho LLMWrapper
        return self._validate_config_with_schema(raw_config, LLMServiceConfig)
        
    def get_feature_store_config(self, file_path: str) -> FeatureStoreConfig:
        """Loads and validates the Feature Store Config (Quality Gate for RAG)."""
        raw_config = self.load_yaml(file_path)
        # FeatureStoreConfig là schema root cho Feature Store
        return self._validate_config_with_schema(raw_config, FeatureStoreConfig)

    def get_rag_prompt_config(self, file_path: str) -> RAGPromptConfig:
        """Loads and validates the RAG Prompt Config."""
        raw_config = self.load_yaml(file_path)
        return self._validate_config_with_schema(raw_config, RAGPromptConfig)
        
    def get_raw_config_by_type(self, type_key: str, config_data: Union[str, Dict[str, Any]]) -> BaseModel:
        """
        Loads a specific component config by type (e.g., loading an OpenAILLMConfig from a map).
        
        Args:
            type_key: 'openai', 'sql_db', etc.
            config_data: File path to a YAML or a raw dictionary.
        """
        # Giả định logic phức tạp để tìm schema class từ GLOBAL_REGISTRY và validate
        
        # Ví dụ tìm schema class (Giả lập)
        if type_key == "openai":
            schema_class = ROOT_CONFIGS["llm_types"]["openai"] 
        else:
            raise KeyError(f"Type key '{type_key}' not found in registry.")

        if isinstance(config_data, str):
            raw_config = self.load_yaml(config_data)
        else:
            raw_config = config_data
            
        return self._validate_config_with_schema(raw_config, schema_class)