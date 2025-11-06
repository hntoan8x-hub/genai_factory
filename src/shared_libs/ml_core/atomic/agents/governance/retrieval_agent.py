# shared_libs/atomic/agents/governance/retrieval_agent.py

from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_llm import BaseLLM
from shared_libs.base.base_tool import BaseTool
from shared_libs.atomic.agents.framework.react_agent import ReActAgent
from typing import List, Optional, Dict, Any

class RetrievalAgent(ReActAgent):
    """
    Agent chuyên biệt trong việc truy vấn dữ liệu từ các nguồn RAG/Database. 
    Nó kế thừa ReActAgent để thực hiện vòng lặp Thought-Act-Observe 
    nhưng chỉ với các Tools truy vấn (RAG/Database).
    Vai trò: Tầng 2 (Specialist Worker) - Truy cập dữ liệu.
    """

    @property
    def name(self) -> str:
        return "data_retrieval_agent"

    @property
    def description(self) -> str:
        return (
            "You are a Data Retrieval Specialist. Your sole purpose is to use the provided "
            "retrieval and query tools (document_search, file_reader, knowledge_db_query) "
            "to accurately find and summarize the requested information in a concise format. "
            "DO NOT answer questions based on general knowledge."
        )

    def __init__(self, llm: BaseLLM, tools: List[BaseTool], max_loops: int = 5):
        """
        Khởi tạo RetrievalAgent. Giới hạn max_loops thấp hơn (5) vì truy vấn RAG nên nhanh.
        """
        
        # 🚨 LOGIC CỨNG HÓA: Kiểm tra Tool Type nếu cần thiết (ví dụ: chỉ cho phép 'retrieval' tools)
        # Bỏ qua kiểm tra type ở đây, nhưng khuyến nghị trong thực tế.
        
        # Kế thừa toàn bộ logic ReAct từ Tầng 1
        super().__init__(llm, tools, max_loops)
        
    async def async_run_query(self, query: str, timeout: Optional[int] = 30) -> str:
        """
        Phương thức đơn giản hóa để chạy tác vụ truy vấn, sử dụng lại async_loop của ReActAgent.
        Đây là phương thức mà Supervisor Agent (Tầng 3) sẽ gọi.
        """
        try:
            self.history = [] # Reset history cho tác vụ mới
            
            # Sử dụng async_loop của ReActAgent (đã được kiểm soát resource)
            result = await self.async_loop(user_input=query, max_steps=self.max_loops, timeout=timeout)
            
            # Xử lý kết quả trả về: đảm bảo chỉ lấy Final Answer
            if "Final Answer:" in result:
                return result.split("Final Answer:")[1].strip()
            
            # Xử lý khi vòng lặp không đạt được Final Answer
            return f"Retrieval Failed: Could not find final answer within max steps. Loop output: {result[:200]}..."

        except asyncio.TimeoutError:
            return f"Retrieval Failed: Query timed out after {timeout} seconds."
        except Exception as e:
            return f"Retrieval Failed due to internal error: {e}"

    # --- BaseAgent Abstract Methods ---
    # Giữ nguyên các phương thức loop/async_loop/plan/act/observe của ReActAgent
    # (vì RetrievalAgent sử dụng mô hình ReAct để thực hiện truy vấn)
    
    # Ghi đè phương thức loop/async_loop để cung cấp interface rõ ràng hơn
    def loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        raise NotImplementedError("Use the asynchronous method 'async_run_query' instead for production stability.")

    async def async_loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        return await self.async_run_query(user_input, timeout)