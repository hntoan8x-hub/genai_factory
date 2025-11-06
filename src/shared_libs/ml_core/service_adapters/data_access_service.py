# shared_libs/service_adapters/data_access_service.py

import asyncio
from typing import Dict, Any, List, Optional
from shared_libs.base.base_tool import BaseTool
from shared_libs.utils.exceptions import ToolExecutionError

class DataAccessService:
    """
    Service Adapter chuyên biệt xử lý tất cả các Tool I/O liên quan đến dữ liệu 
    (DB, RAG, File, API). Mục tiêu là quản lý các pool kết nối tối ưu.
    """
    
    def __init__(self, tools: Dict[str, BaseTool]):
        """Khởi tạo với các Tool Data Access được cấp quyền."""
        self.data_access_tools = {t.name: t for t in tools if self._is_data_tool(t.name)}
        if not self.data_access_tools:
            print("Warning: DataAccessService initialized with no data access tools.")

    def _is_data_tool(self, name: str) -> bool:
        """Helper xác định Tool có thuộc Data Access không."""
        return name in ["sql_query_executor", "document_retriever", "file_reader", "data_api_connector"]

    async def execute_async(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực thi Tool Data Access bất đồng bộ.
        """
        tool = self.data_access_tools.get(tool_name)
        if not tool:
            raise ToolExecutionError(f"Tool '{tool_name}' not found or unauthorized for DataAccessService.")

        try:
            # Gọi phương thức async_run của Tool.
            # Lưu ý: Các Tool I/O đồng bộ (như SQLTool) đã tự handle ThreadPoolExecutor bên trong.
            return await tool.async_run(tool_input)
        except Exception as e:
            raise ToolExecutionError(f"DataAccess Tool '{tool_name}' execution error: {str(e)}")
            
# --- END DataAccessService ---