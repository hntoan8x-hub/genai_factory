# shared_libs/factory/tool_factory.py (FINAL HARDENED VERSION - Cập nhật)

from typing import Dict, Any, Union, Type, List, Optional
from shared_libs.base.base_tool import BaseTool
from shared_libs.utils.exceptions import GenAIFactoryError

# --- Import Tools (Giữ nguyên) ---
from shared_libs.atomic.tools.data_access.read_only.sql_query_executor import SQLTool 
from shared_libs.atomic.tools.analysis_compute.risk_tool import RiskTool 
from shared_libs.atomic.tools.external_world.web_tool import WebTool 
from shared_libs.atomic.tools.analysis_compute.calculator_tool import CalculatorTool 
from shared_libs.atomic.tools.external_world.email_tool import EmailTool 
from shared_libs.atomic.tools.data_access.read_only.data_api_connector import DataAPIConnector
from shared_libs.atomic.tools.analysis_compute.statistical_visualizer import StatisticalVisualizer
from shared_libs.atomic.tools.external_world.slack_notifier import SlackNotifier
from shared_libs.atomic.tools.file_storage.file_reader import FileReader
from shared_libs.atomic.tools.file_storage.json_xml_parser import JSONXMLParser
from shared_libs.atomic.tools.internal_rag.document_retriever_tool import DocumentRetrieverTool
from shared_libs.atomic.tools.analysis_compute.data_analyzer_tool import DataAnalyzerTool
# 🚨 Tool Governance
from shared_libs.atomic.tools.governance_utils.audit_tool import AuditTool 
from shared_libs.atomic.tools.governance_utils.cache_tool import CacheTool 
# Import Dependencies cần thiết
from shared_libs.base.base_llm import BaseLLM
from shared_libs.feature_store.base.base_retriever import BaseRetriever
# Import Schemas từ __init__.py (Public API)
from shared_libs.configs.schemas import ToolName, ToolBaseConfig, SQLToolConfig, EmailToolConfig, SlackToolConfig, AuditToolConfig, CacheToolConfig
from pydantic import BaseModel # Cần cho type hinting

# Định nghĩa Union cho các loại Tool Config Models được chấp nhận
ToolConfigModel = Union[SQLToolConfig, EmailToolConfig, SlackToolConfig, AuditToolConfig, CacheToolConfig, ToolBaseConfig, BaseModel]

class ToolFactory:
    
    def __init__(self):
        self._tool_types: Dict[str, Type[BaseTool]] = {
            "sql": SQLTool, "risk": RiskTool, "web": WebTool, "calculator": CalculatorTool,
            "email": EmailTool, "api_connector": DataAPIConnector, "visualizer": StatisticalVisualizer,
            "slack": SlackNotifier, "file_reader": FileReader, "parser": JSONXMLParser,
            "rag": DocumentRetrieverTool, "analyzer": DataAnalyzerTool,
            # Governance Tools
            "audit": AuditTool, "cache": CacheTool,
        }

    # Cập nhật signature để nhận thêm **kwargs cho Dependency Injection
    def build(self, config_model: Optional[ToolConfigModel] = None, **kwargs) -> BaseTool:
        """
        Builds a Tool instance, supporting direct Dependency Injection via kwargs 
        (e.g., for RAG components).
        """
        
        # 1. Xác định Tool Type
        if config_model:
            tool_type = config_model.type.value if hasattr(config_model.type, 'value') else config_model.type
        elif 'tool_type' in kwargs:
            # Cho phép override type qua kwargs cho DI, ví dụ: 'document_retriever'
            tool_type = kwargs.get('tool_type') 
        else:
            raise ValueError("Must provide either a config_model or 'tool_type' in kwargs.")

        if tool_type not in self._tool_types and tool_type != 'document_retriever': # Thêm check cho tên class
            raise ValueError(f"Unsupported Tool type: {tool_type}.")
        
        tool_class = self._tool_types.get(tool_type, DocumentRetrieverTool)
        
        # 2. Xử lý Dependency Injection cho DocumentRetrieverTool
        if tool_class is DocumentRetrieverTool:
            # Kiểm tra các Dependencies bắt buộc (đã được tiêm từ RAGPipeline)
            retriever_instance = kwargs.get('retriever_instance')
            embedding_llm = kwargs.get('embedding_llm')
            
            if not isinstance(retriever_instance, BaseRetriever) or not isinstance(embedding_llm, BaseLLM):
                 raise GenAIFactoryError("RAG Tool initialization failed: Missing required BaseRetriever or BaseLLM dependency injection.")
            
            try:
                # Trả về DocumentRetrieverTool đã được inject
                return DocumentRetrieverTool(
                    retriever_instance=retriever_instance, 
                    embedding_llm=embedding_llm
                )
            except Exception as e:
                raise GenAIFactoryError(f"Error initializing RAG Tool via injection: {e}")
        
        # 3. Xử lý Khởi tạo Tool thông thường (Sử dụng config_model)
        if config_model is None:
             raise ValueError(f"Tool type '{tool_type}' requires a Pydantic configuration model.")

        init_params = config_model.model_dump(exclude_none=True, exclude={'type', 'name'})
        
        try:
            # SỬ DỤNG UNPACKING cho các Tool thông thường
            return tool_class(**init_params)
            
        except TypeError as e:
            raise GenAIFactoryError(f"Error initializing Tool '{tool_type}': Check Tool's __init__ signature. Detail: {e}")
        except Exception as e:
            raise GenAIFactoryError(f"Unexpected error during Tool '{tool_type}' initialization: {e}")