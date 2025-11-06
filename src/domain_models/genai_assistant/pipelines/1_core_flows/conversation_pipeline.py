# GenAI_Factory/src/domain_models/genai_assistant/pipelines/1_core_flows/conversation_pipeline.py

import logging
from typing import Dict, Any, Optional
import time 
from shared_libs.factory.llm_factory import LLMFactory
from shared_libs.base.base_llm import BaseLLM
from shared_libs.utils.exceptions import GenAIFactoryError, LLMAPIError

# Import các Schema và Service đã được Hardening
from domain_models.genai_assistant.services.memory_service import MemoryService
from domain_models.genai_assistant.schemas.conversation_schema import ConversationHistory, ConversationTurn 

logger = logging.getLogger(__name__)

class ConversationPipeline:
    """
    Manages a multi-turn conversation, incorporating structured memory for context.
    
    This pipeline uses Pydantic Schemas as the Quality Gate for all data flowing 
    in and out of the memory store, and executes asynchronously for performance.
    """
    
    def __init__(self, config: Dict[str, Any], llm_instance: BaseLLM, memory_service: MemoryService):
        """
        Initializes the pipeline.
        
        Args:
            config: General configuration dictionary.
            llm_instance: The Hardened BaseLLM instance (built by LLMFactory).
            memory_service: The Hardened MemoryService instance.
        """
        self.config = config
        self.llm = llm_instance
        self.memory = memory_service
        self.max_turns = config.get("max_conversation_turns", 10)

    async def async_run(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Executes the conversation pipeline asynchronously.
        """
        logger.info(f"[{user_id}] Executing conversation pipeline.")
        
        # 1. Retrieve conversation history (sẽ trả về ConversationHistory Schema hoặc None)
        try:
            history_schema: Optional[ConversationHistory] = await self.memory.async_retrieve(user_id)
            if not history_schema:
                 # Khởi tạo Schema mới nếu không tìm thấy lịch sử
                 history_schema = ConversationHistory(session_id=user_id, history=[])
        except GenAIFactoryError as e:
            logger.error(f"Failed to retrieve memory for {user_id}: {e}. Proceeding with empty context.")
            # Quan trọng: Tiếp tục với lịch sử trống nếu lỗi bộ nhớ không phải là lỗi fatal
            history_schema = ConversationHistory(session_id=user_id, history=[]) 

        # 2. Add current query to history (Sử dụng ConversationTurn Schema)
        user_turn = ConversationTurn(role="user", content=query, timestamp=time.time())
        history_schema.history.append(user_turn)
        
        # 3. Chuẩn bị Context cho LLM
        
        # Cắt bớt lịch sử nếu quá dài (Hardening: Tối ưu độ trễ/chi phí)
        if len(history_schema.history) > self.max_turns:
            # Chỉ giữ lại N lượt cuối cùng
            history_schema.history = history_schema.history[-self.max_turns:]
            logger.warning(f"Conversation history truncated to {self.max_turns} turns.")

        # Chuyển đổi lịch sử có cấu trúc thành format dễ đọc cho LLM
        context_messages = [
            f"{t.role.capitalize()}: {t.content}" for t in history_schema.history
        ]
        full_context_prompt = "\n".join(context_messages)
        
        # 4. Generate a response from the LLM 
        logger.info(f"[{user_id}] Generating response from LLM...")
        try:
            # Sử dụng async_generate của LLM instance đã được Hardening (với retry/fallback)
            response_content = await self.llm.async_generate(prompt=full_context_prompt)
        except LLMAPIError as e:
            logger.error(f"LLM API failure for {user_id}: {e}")
            # Chuyển đổi lỗi LLM thành lỗi Framework để AssistantService xử lý
            raise GenAIFactoryError("Failed to generate response due to LLM backend error.") from e
        except Exception as e:
             logger.error(f"Unknown generation failure for {user_id}: {e}")
             raise GenAIFactoryError("Unknown error during LLM generation.") from e


        # 5. Add the LLM's response to history (Sử dụng ConversationTurn Schema)
        assistant_turn = ConversationTurn(role="assistant", content=response_content, timestamp=time.time())
        history_schema.history.append(assistant_turn)
        
        # 6. Store the updated history (truyền Schema đã được cập nhật cho MemoryService)
        # MemoryService sẽ xử lý Token Limiting và Summarization (CRITICAL COST CONTROL)
        await self.memory.async_store(user_id, history_schema)
        
        logger.info(f"[{user_id}] Conversation pipeline completed. History stored.")
        
        # Trả về kết quả với metadata đầy đủ
        return {
            "response": response_content,
            "metadata": {
                "session_id": user_id,
            },
            "pipeline": "conversation_pipeline"
        }