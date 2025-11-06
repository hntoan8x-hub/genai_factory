# shared_libs/atomic/tools/governance_utils/cache_tool.py

from shared_libs.base.base_tool import BaseTool
from shared_libs.configs.schemas import CacheToolConfig # Import Config
from typing import Dict, Any, Optional
import asyncio
import logging
import json

logger = logging.getLogger(__name__)

class CacheTool(BaseTool):
    """
    Tool chuyên biệt cung cấp giao diện bất đồng bộ để lưu trữ và truy xuất 
    kết quả của các Tool Call (Sử dụng Redis/Memcached/v.v.). (GOVERNANCE UTILITY)
    """

    @property
    def name(self) -> str:
        return "cache_tool"

    @property
    def description(self) -> str:
        return "Stores and retrieves previous tool execution results using a simple key-value cache."

    def __init__(self, redis_connection_string: str, default_ttl_seconds: int, **kwargs):
        """
        Khởi tạo Cache Tool.
        Args:
            redis_connection_string (str): Chuỗi kết nối đến dịch vụ Cache (ví dụ: Redis).
            default_ttl_seconds (int): Thời gian sống mặc định (TTL).
        """
        super().__init__(**kwargs)
        self.redis_connection_string = redis_connection_string
        self.default_ttl = default_ttl_seconds
        # Trong production, self.cache_client sẽ là một instance Redis client bất đồng bộ (ví dụ: aioredis)
        self._is_connected = True

    async def _mock_cache_io(self, action: str, key: str, value: Optional[str] = None, ttl: Optional[int] = None) -> Optional[str]:
        """Mô phỏng I/O bất đồng bộ đến Cache Service."""
        await asyncio.sleep(0.01) # Mô phỏng độ trễ I/O rất nhỏ
        
        if action == "GET":
            # Trong thực tế, nếu tìm thấy key, trả về data
            if key.startswith("sql:"): # Giả định key SQL luôn có Cache Hit
                return json.dumps({"cached_data": "MOCK_SQL_RESULT"})
            return None 
        elif action == "SET":
            logger.debug(f"Cache SET: key={key} with TTL={ttl or self.default_ttl}")
            return "OK"
        return None

    async def async_run(self, tool_input: Dict[str, Any]) -> Optional[str]:
        """
        Thực hiện thao tác Cache (GET hoặc SET).

        Tool Input Format:
        { "action": "GET"/"SET", "key": "...", "value": "...", "ttl": 3600 }
        """
        action = tool_input.get("action", "").upper()
        key = tool_input.get("key")
        value = tool_input.get("value")
        ttl = tool_input.get("ttl")

        if not key:
            raise ValueError("Cache operation requires a 'key'.")

        try:
            if action == "GET":
                result = await self._mock_cache_io("GET", key)
                return result # Trả về chuỗi JSON/string hoặc None
            
            elif action == "SET" and value is not None:
                await self._mock_cache_io("SET", key, value, ttl)
                return "Observation: Cache entry set successfully."
            
            return f"Observation: Invalid cache action '{action}'."

        except Exception as e:
            logger.error(f"Cache operation failed for key {key}: {e}")
            # Cache failure không nên làm sập Agent, nên trả về None
            return None 

    def run(self, tool_input: Dict[str, Any]) -> str:
        """Phương thức đồng bộ (chỉ để hoàn thành BaseTool contract, khuyến khích dùng async)."""
        raise NotImplementedError("Use the asynchronous method 'async_run' for Cache operations.")