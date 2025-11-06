# GenAI_Factory/src/domain_models/genai_assistant/services/memory_service.py

import logging
import asyncio
from typing import Any, Dict, List, Optional
from shared_libs.base.base_memory import BaseMemory
from shared_libs.base.base_llm import BaseLLM # Cần cho việc tóm tắt
from shared_libs.utils.exceptions import GenAIFactoryError
from aioredis import Redis, exceptions as RedisExceptions 

# Import Schemas đã được Hardening
from domain_models.genai_assistant.schemas.config_schemas import AssistantConfigSchema 
from domain_models.genai_assistant.schemas.conversation_schema import ConversationHistory 

logger = logging.getLogger(__name__)

# Giả định TokenLimiter là một class có phương thức count_tokens()
class DummyTokenLimiter:
    @staticmethod
    def count_tokens(text: str) -> int:
        """Mô phỏng việc đếm token cho văn bản."""
        return len(text.split()) * 1.5 

class MemoryService(BaseMemory):
    """
    Manages long-term conversation memory using an asynchronous Redis store.
    Implements token control to prevent excessive cost accumulation. (CRITICAL HARDENING)
    """

    def __init__(self, config: AssistantConfigSchema, redis_url: str, llm_instance: BaseLLM):
        """
        Initializes the MemoryService.

        Args:
            config (AssistantConfigSchema): Cấu hình đã được xác thực.
            redis_url (str): URL kết nối Redis.
            llm_instance (BaseLLM): Instance LLM (dùng cho việc tóm tắt).
        """
        self.config = config
        self.max_tokens = config.max_history_tokens # Lấy từ Schema đã xác thực
        self.token_limiter = DummyTokenLimiter() 
        self.llm = llm_instance
        
        # Initialize Async Redis client
        try:
             self.client = Redis.from_url(redis_url)
             logger.info(f"MemoryService initialized with Redis at {redis_url}.")
        except Exception as e:
             logger.critical(f"Failed to connect to Redis: {e}")
             raise GenAIFactoryError(f"MemoryService failed to initialize Redis.") from e


    async def async_store(self, key: str, value: ConversationHistory) -> None:
        """
        Asynchronously stores a session value, checking token limits before saving.
        
        Args:
            key (str): Khóa session ID.
            value (ConversationHistory): Schema lịch sử hội thoại đã được cập nhật.
        """
        
        value_str = value.json()
        current_token_count = self.token_limiter.count_tokens(value_str)
        value.total_tokens = int(current_token_count) # Cập nhật tổng token vào Schema
        
        # 1. Kiểm tra giới hạn token trước khi lưu (CRITICAL COST CONTROL)
        if current_token_count > self.max_tokens:
             logger.warning(f"Session {key} exceeded max token limit ({current_token_count} > {self.max_tokens}). Triggering summarization.")
             
             # Hardening: Gọi tóm tắt bất đồng bộ
             await self.async_summarize(key, value) 
             # Cập nhật lại chuỗi JSON sau khi tóm tắt (hoặc chỉ lưu bản tóm tắt)
             value_str = value.json() 

        # 2. Lưu trữ
        try:
            # Lưu trữ dữ liệu Schema đã được cập nhật
            await self.client.set(key, value_str)
            logger.debug(f"Stored session {key} with {value.total_tokens} tokens.")
        except RedisExceptions as e:
            raise GenAIFactoryError(f"Async store failed for key {key} in Redis: {e}")

    async def async_retrieve(self, key: str) -> Optional[ConversationHistory]:
        """
        Asynchronously retrieves a value and parses it into the Pydantic Schema.
        """
        try:
            raw_data = await self.client.get(key)
            if raw_data:
                # XÁC THỰC LẠI DATA ĐÃ LƯU TRỮ (DATA INTEGRITY HARDENING)
                return ConversationHistory.parse_raw(raw_data)
            return None
        except RedisExceptions as e:
            # Lỗi kết nối Redis
            raise GenAIFactoryError(f"Async retrieve failed for key {key}: {e}")
        except Exception:
             # Xử lý lỗi parse (dữ liệu hỏng/không hợp lệ)
             logger.error(f"Failed to parse history for key {key}. Data corrupted. Deleting session.")
             # Thêm logic xóa key hỏng
             await self.client.delete(key) 
             return None

    async def async_summarize(self, key: str, history_schema: ConversationHistory) -> None:
        """
        Asynchronously triggers LLM summarization to condense history, reducing cost.
        """
        # Chuẩn bị prompt tóm tắt
        context_to_summarize = history_schema.history
        
        # Giả định LLM chỉ tóm tắt các turn cũ
        if len(context_to_summarize) <= 2:
            return # Không tóm tắt nếu lịch sử quá ngắn
            
        summary_prompt = "Please concisely summarize the following conversation history:\n" + "\n".join([f"{t.role.capitalize()}: {t.content}" for t in context_to_summarize[:-2]])
        
        try:
            # Gọi LLM bất đồng bộ để tóm tắt
            new_summary = await self.llm.async_generate(prompt=summary_prompt, max_tokens=self.max_tokens // 4)
            
            # Cập nhật Schema: chuyển các turn cũ vào summary và chỉ giữ lại 2 turn mới nhất
            history_schema.summary = new_summary
            history_schema.history = history_schema.history[-2:] 
            
            # Cập nhật lại token count sau khi tóm tắt
            history_schema.total_tokens = self.token_limiter.count_tokens(history_schema.summary + history_schema.history[-1].content)
            
            logger.info(f"Session {key} successfully summarized. New token count: {history_schema.total_tokens}.")
            
        except Exception as e:
            logger.error(f"Failed to summarize memory for {key}: {e}")
            # Decision: Nếu tóm tắt thất bại, vẫn lưu trữ bản đầy đủ (dù tốn kém)
            pass

    # --- Synchronous Methods (Base Class Contract Fulfillment) ---
    def store(self, key: str, value: Any) -> None:
        # Chuyển đổi dict/raw data thành Schema trước khi chạy async
        history = ConversationHistory(**value)
        asyncio.run(self.async_store(key, history)) 
        
    def retrieve(self, key: str) -> Any:
        result = asyncio.run(self.async_retrieve(key))
        return result.dict() if result else None