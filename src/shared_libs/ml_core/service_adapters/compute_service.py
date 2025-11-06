# shared_libs/service_adapters/compute_service.py

import asyncio
from typing import Dict, Any, List, Optional
from shared_libs.base.base_tool import BaseTool
from shared_libs.utils.exceptions import ToolExecutionError
from concurrent.futures import ThreadPoolExecutor

class ComputeService:
    """
    Service Adapter chuyên biệt xử lý các Tool CPU-Bound (Analysis, Risk, Visualization).
    Sử dụng ThreadPoolExecutor riêng để tối ưu hóa việc phân luồng tính toán.
    """
    
    def __init__(self, tools: Dict[str, BaseTool]):
        """Khởi tạo với các Tool Compute được cấp quyền."""
        self.compute_tools = {t.name: t for t in tools if self._is_compute_tool(t.name)}
        if not self.compute_tools:
            print("Warning: ComputeService initialized with no compute tools.")
        
        # Khởi tạo ThreadPoolExecutor riêng cho tác vụ CPU
        self.executor = ThreadPoolExecutor(max_workers=4) 

    def _is_compute_tool(self, name: str) -> bool:
        """Helper xác định Tool có thuộc Compute không."""
        return name in ["data_analyzer", "statistical_visualizer", "risk_tool", "calculator_tool", "json_xml_parser"]

    async def execute_async(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực thi Tool Compute bất đồng bộ bằng cách offload sang ThreadPoolExecutor.
        """
        tool = self.compute_tools.get(tool_name)
        if not tool:
            raise ToolExecutionError(f"Tool '{tool_name}' not found or unauthorized for ComputeService.")

        loop = asyncio.get_event_loop()
        
        try:
            # Offload synchronous run() của Tool (vì chúng là CPU-Bound)
            # Điều này tách biệt luồng xử lý CPU khỏi luồng mạng I/O
            return await loop.run_in_executor(
                self.executor,
                tool.run, # Gọi phương thức run() đồng bộ của Tool
                tool_input
            )
        except Exception as e:
            raise ToolExecutionError(f"Compute Tool '{tool_name}' execution error: {str(e)}")
            
# --- END ComputeService ---