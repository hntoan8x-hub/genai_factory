# shared_libs/configs/schemas/__init__.py (FINAL VERSION - Public API & Registry)

from pydantic import BaseModel
from typing import Dict, Any, Union, List
from enum import Enum

# --- 1. ENUMS (Ngôn ngữ chung cho toàn bộ Factory) ---

class LLMType(str, Enum):
    """Định danh các nhà cung cấp LLM."""
    OPENAI = 'openai'
    ANTHROPIC = 'anthropic'
    HUGGINGFACE = 'huggingface'

class ToolName(str, Enum):
    """Định danh tất cả các Tools trong Factory."""
    # Tools Nghiệp vụ/Thực thi
    SQL_EXECUTOR = 'sql_query_executor'
    WEB_SEARCH = 'web_tool'
    EMAIL_SENDER = 'email_tool'
    RISK_MODEL = 'risk_tool'
    CALCULATOR = 'calculator_tool'
    DATA_API_CONNECTOR = 'data_api_connector'
    DOCUMENT_RETRIEVER = 'document_retriever'
    # Tools Governance/Utility
    AUDIT_TOOL = 'audit_tool'
    CACHE_TOOL = 'cache_tool'
    SLACK_NOTIFIER = 'slack_notifier'
    FILE_READER = 'file_reader'
    JSON_XML_PARSER = 'json_xml_parser'


# --- 2. IMPORTS TỪ CÁC MODULE CON (Gom Logic) ---

# Imports từ tool_input_output.py
from .tool_input_output import TOOL_INPUT_MAP, ToolInputBase, ToolOutputBase

# Imports từ agent_config.py
from .agent_config import AGENT_CONFIG_MAP, AgentBaseConfig, ReActAgentConfig, SupervisorAgentConfig, CriticAgentConfig

# Imports từ tool_config.py
from .tool_config import ToolBaseConfig, SQLToolConfig, EmailToolConfig, SlackToolConfig, AuditToolConfig, CacheToolConfig

# Imports từ llm_config.py
from .llm_config import LLMServiceConfig, OpenAILLMConfig

# Imports từ evaluator_config.py
from .evaluator_config import EVALUATOR_CONFIG_MAP, EvaluatorConfigSchema

# 🚨 BỔ SUNG: Imports từ monitoring_config.py
from .monitoring_config import MONITORING_CONFIG_MAP, CostMonitorConfig, AlertAdapterConfig

from .memory_config import MEMORY_CONFIG_MAP, RedisMemoryConfig, SQLMemoryConfig
# --- 3. THE CENTRAL REGISTRY CLASS (CRITICAL HARDENING) ---
class SchemaRegistry:
    """
    Registry trung tâm cung cấp quyền truy cập được kiểm soát vào tất cả các Pydantic Schemas.
    """
    TOOL_INPUT_MAP: Dict[ToolName, type[BaseModel]] = TOOL_INPUT_MAP
    AGENT_CONFIG_MAP: Dict[str, type[BaseModel]] = AGENT_CONFIG_MAP
    EVALUATOR_CONFIG_MAP: Dict[str, type[BaseModel]] = EVALUATOR_CONFIG_MAP
    
    # 🚨 BỔ SUNG: Thêm MONITORING MAP
    MONITORING_CONFIG_MAP: Dict[str, type[BaseModel]] = MONITORING_CONFIG_MAP
    
    MEMORY_CONFIG_MAP: Dict[str, type[BaseModel]] = MEMORY_CONFIG_MAP
    
    @staticmethod
    def get_tool_input_schema(tool_name: str) -> type[BaseModel]:
        """Truy xuất Schema Input Pydantic cho Tool (dùng để Validation Tool Call)."""
        try:
            return SchemaRegistry.TOOL_INPUT_MAP[ToolName(tool_name.lower())]
        except ValueError:
            raise ValueError(f"ToolName '{tool_name}' không hợp lệ hoặc không có Schema Input.")
        except KeyError:
            return ToolInputBase 

    @staticmethod
    def get_agent_config_schema(agent_name: str) -> type[BaseModel]:
        """Truy xuất Schema Config Pydantic cho Agent (dùng để Validation Khởi tạo)."""
        agent_name = agent_name.lower().replace("_agent", "")
        return SchemaRegistry.AGENT_CONFIG_MAP.get(agent_name, AgentBaseConfig)


# --- 4. EXPORT CÁC THÀNH PHẦN CHÍNH (Tạo Public API) ---
__all__ = [
    # Enums
    'LLMType', 'ToolName',
    # Registry
    'SchemaRegistry',
    # Base Configs
    'AgentBaseConfig', 'ToolBaseConfig', 'ToolInputBase', 'ToolOutputBase',
    # Specialized Configs
    'ReActAgentConfig', 'SupervisorAgentConfig', 'CriticAgentConfig',
    'SQLToolConfig', 'SlackToolConfig', 'AuditToolConfig', 'CacheToolConfig',
    'LLMServiceConfig', 'OpenAILLMConfig',
    'EvaluatorConfigSchema',
    # 🚨 BỔ SUNG: Monitoring Configs
    'CostMonitorConfig', 'AlertAdapterConfig',
    'RedisMemoryConfig', 'SQLMemoryConfig'
    
]