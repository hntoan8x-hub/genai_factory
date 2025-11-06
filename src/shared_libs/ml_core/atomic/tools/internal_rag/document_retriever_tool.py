# shared_libs/atomic/tools/internal_rag/document_retriever_tool.py
import asyncio
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field
from shared_libs.base.base_tool import BaseTool
from shared_libs.base.base_llm import BaseLLM # Dependency
from shared_libs.feature_store.base.base_retriever import BaseRetriever # Dependency
from shared_libs.utils.exceptions import ToolExecutionError

# --- Pydantic Schemas ---
class RetrievalInput(BaseModel):
    """Schema for the input of the Document Retrieval Tool."""
    query: str = Field(..., description="The natural language query to search internal documents.")
    policy_type: Optional[str] = Field(None, description="Optional: Filter search to a specific policy type (e.g., 'credit_risk', 'market_risk').")
    max_results: int = Field(5, description="The maximum number of document snippets to retrieve.")

class RetrievedDocument(BaseModel):
    """Schema for a single retrieved document snippet."""
    source_id: str = Field(..., description="The unique ID or title of the source document.")
    snippet: str = Field(..., description="The relevant text snippet from the document.")
    score: float = Field(..., description="The relevance score of the snippet.")

class RetrievalOutput(BaseModel):
    """Schema for the output of the Document Retrieval Tool."""
    retrieved_documents: List[RetrievedDocument] = Field(..., description="A list of relevant document snippets.")

# --- Tool Implementation ---
class DocumentRetrieverTool(BaseTool):
    """
    Adapter tool: Converts user query (text) into search results (retrieved documents) 
    by coordinating the LLM (Embedding) and the Feature Store (Retrieval).
    """
    
    def __init__(self, retriever_instance: BaseRetriever, embedding_llm: BaseLLM):
        """
        Hardening 1: Initializes the Tool via Dependency Injection.
        """
        self.retriever_component = retriever_instance
        self.embedding_llm = embedding_llm
        
        # NOTE: Các Tool không gọi super().__init__(**kwargs) nếu không cần config riêng

    @property
    def name(self) -> str:
        return "document_retriever"
    
    @property
    def description(self) -> str:
        return "Retrieves relevant text snippets from the internal document knowledge base using vector search."

    @property
    def input_schema(self) -> BaseModel:
        return RetrievalInput

    @property
    def output_schema(self) -> BaseModel:
        return RetrievalOutput

    # --- Internal Execution (Synchronous Placeholder) ---
    def _execute(self, validated_input: RetrievalInput) -> Dict[str, Any]:
        """Synchronous core logic (Not preferred in this factory)."""
        # Để tuân thủ BaseTool, ta phải triển khai, nhưng nên gọi async_run
        return asyncio.run(self._async_execute(validated_input))

    # --- Internal Asynchronous Execution (HARDENING - Preferred Method) ---
    async def _async_execute(self, validated_input: RetrievalInput) -> Dict[str, Any]:
        """
        Asynchronously executes the retrieval: Embed -> Search.
        """
        try:
            query = validated_input.query
            k = validated_input.max_results
            
            # 1. Query Embedding (Sử dụng BaseLLM.async_embed)
            query_vector_list = await self.embedding_llm.async_embed(query)
            query_vector = np.array(query_vector_list)
            
            # 2. Asynchronous Retrieval (Sử dụng BaseRetriever.async_retrieve)
            # Logic filtering metadata (policy_type) phải được xử lý bên trong BaseRetriever
            retrieved_data = await self.retriever_component.async_retrieve(
                query_vector=query_vector,
                k=k,
                # Giả định BaseRetriever chấp nhận tham số filter trong **kwargs
                filter_params={"policy_type": validated_input.policy_type} 
            )

            # 3. Output Validation & Formatting (retrieved_data đã là List[Dict[...]])
            return RetrievalOutput(retrieved_documents=retrieved_data).model_dump()
            
        except Exception as e:
            # Chuyển đổi lỗi thành ToolExecutionError
            raise ToolExecutionError(f"RAG Retrieval failed during execution: {e.__class__.__name__}: {str(e)}")