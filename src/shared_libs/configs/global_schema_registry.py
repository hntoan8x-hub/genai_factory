# src/shared_libs/configs/global_schema_registry.py (Centralized Registry)

from typing import Dict, Type, Union
from pydantic import BaseModel

# --- Import and combine all specialized registries ---
from shared_libs.configs.schemas.llm_config import LLM_CONFIG_MAP
from shared_libs.configs.schemas.tool_config import TOOL_CONFIG_MAP
from shared_libs.configs.schemas.evaluator_config import EVALUATOR_CONFIG_MAP
from shared_libs.configs.schemas.memory_config import MEMORY_CONFIG_MAP
from shared_libs.configs.schemas.monitoring_config import MONITORING_CONFIG_MAP
# Giả định các schema khác (Feature Store, Agent, Ingestion) cũng được import:
from shared_libs.feature_store.configs.feature_store_config_schema import FeatureStoreConfig 
from shared_libs.configs.schemas.agent_config import AGENT_CONFIG_MAP 
from shared_libs.configs.schemas.utility_config import RAGPromptConfig, EvaluatorConfigSchema

# ----------------------------------------------------
# GLOBAL SCHEMA REGISTRY (SINGLE SOURCE OF TRUTH)
# ----------------------------------------------------
# Khai báo các class Pydantic chính mà ConfigLoader sẽ trả về
# Thay vì các map con, ta dùng các class cha đại diện

# Mapping các loại cấu hình chính (Root Configs)
ROOT_CONFIGS: Dict[str, Type[BaseModel]] = {
    # 1. Pipeline/Tool/Agent Framework Roots
    "feature_store": FeatureStoreConfig,
    "evaluator_schema": EvaluatorConfigSchema,
    "rag_prompt": RAGPromptConfig,
    
    # 2. Component Type Maps (Đại diện cho các Enum/Type)
    "llm_types": LLM_CONFIG_MAP,
    "agent_types": AGENT_CONFIG_MAP,
    "tool_types": TOOL_CONFIG_MAP,
    "memory_types": MEMORY_CONFIG_MAP,
    "monitoring_types": MONITORING_CONFIG_MAP,
    
    # NOTE: RAG Ingestion Config và LLM Service Config sẽ được thêm vào đây
}