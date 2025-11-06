# GenAI_Factory/src/domain_models/genai_assistant/pipelines/1_core_flows/rag_pipeline.py

import logging
from typing import Dict, Any, List
from shared_libs.factory.llm_factory import LLMFactory
from shared_libs.factory.prompt_factory import PromptFactory
from shared_libs.base.base_llm import BaseLLM
from shared_libs.base.base_tool import BaseTool # Thêm BaseTool cho Retriever
from shared_libs.factory.tool_factory import ToolFactory # Thêm ToolFactory cho Retriever
from shared_libs.utils.exceptions import GenAIFactoryError, LLMAPIError, ToolExecutionError
from domain_models.genai_assistant.schemas.config_schemas import RetrieverConfigSchema, LLMConfigSchema 

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    Implements a Retrieval-Augmented Generation (RAG) pipeline for production.

    It uses validated configurations and executes all steps asynchronously to ensure
    high concurrency and performance. (HARDENING: Async Architecture)
    """

    def __init__(self, llm_config: LLMConfigSchema, retriever_config: RetrieverConfigSchema, rag_prompt_config: Dict[str, Any]):
        """
        Initializes the RAGPipeline with validated configuration Schemas.
        """
        self.llm_config = llm_config
        self.retriever_config = retriever_config
        self.rag_prompt_config = rag_prompt_config
        
        # 1. Khởi tạo LLM (Đảm bảo có Resilience/Fallback)
        # LLMFactory sử dụng config đã xác thực để tạo LLM instance Hardened
        self.llm: BaseLLM = LLMFactory.build(self.llm_config.dict()) 
        self.rag_prompt = PromptFactory.build(self.rag_prompt_config)
        
        # 2. Thiết lập Retriever (Sử dụng ToolFactory để tạo instance Vector DB/Retriever Tool)
        # ToolFactory sẽ sử dụng retriever_config để khởi tạo kết nối an toàn
        self.retriever: BaseTool = self._setup_retriever()
        
        # Giới hạn số lượng tài liệu truy xuất (lấy từ Schema)
        self.top_k = self.retriever_config.top_k_retrieval 
        
        logger.info(f"RAGPipeline initialized. Model: {self.llm_config.model_name}, Top-K: {self.top_k}")

    def _setup_retriever(self) -> BaseTool:
        """
        Instantiates the Retriever Tool using ToolFactory.
        This ensures the retriever connection details are secure and validated.
        """
        # Giả định ToolFactory có khả năng tạo Retriever Tool từ config
        try:
            # Truyền config endpoint đã được xác thực
            retriever_tool = ToolFactory.build({
                "type": "vector_db_retriever",
                "config": self.retriever_config.dict() 
            })
            return retriever_tool
        except Exception as e:
            logger.critical(f"FATAL: Failed to initialize Retriever Tool: {e}")
            raise GenAIFactoryError(f"Retriever initialization failed.") from e


    async def async_run(self, query: str) -> Dict[str, Any]:
        """
        Executes the RAG pipeline asynchronously (CRITICAL HARDENING).
        """
        logger.info("Executing RAG pipeline async...")
        
        retrieved_text: str = ""
        sources: List[str] = []
        
        # 1. Retrieve relevant context (Async Execution)
        try:
            # Giả định BaseTool.async_run() nhận query và trả về list documents
            retrieval_result: Dict[str, Any] = await self.retriever.async_run(
                {"query": query, "top_k": self.top_k}
            )
            
            # Trích xuất dữ liệu
            documents = retrieval_result.get("documents", [])
            retrieved_text = "\n\n".join([doc.get("content", "") for doc in documents])
            sources = [doc.get("source", "N/A") for doc in documents]
            
            if not retrieved_text:
                logger.warning("No relevant documents retrieved. Generating response without context.")

        except ToolExecutionError as e:
            logger.error(f"Retriever execution failed: {e}")
            # Có thể quyết định tiếp tục với context rỗng hoặc ném lỗi
            retrieved_text = f"Warning: Retrieval system failed: {e}. Answering based on general knowledge."
            sources = ["Retrieval system failed"]

        # 2. Render the prompt with the retrieved context
        rendered_prompt = self.rag_prompt.render(
            context={"context": retrieved_text, "question": query}
        )
        
        # 3. Generate a response from the LLM (Async Execution)
        logger.info("Generating grounded response...")
        try:
            # Sử dụng async_generate của LLM instance đã được Hardening (với retry/fallback)
            response = await self.llm.async_generate(prompt=rendered_prompt)
        except LLMAPIError as e:
            logger.error(f"LLM API failure in RAG pipeline: {e}")
            # Chuyển đổi lỗi LLM thành lỗi Framework để AssistantService xử lý
            raise GenAIFactoryError("Failed to generate response due to LLM backend error.") from e
        
        logger.info("RAG pipeline completed.")
        
        # Trả về kết quả với metadata đầy đủ
        return {
            "response": response,
            "metadata": {
                "sources": sources,
                "model": self.llm_config.model_name
            },
            "pipeline": "rag_pipeline"
        }