# shared_libs/atomic/agents/framework/planning_agent.py

from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_llm import BaseLLM
from typing import Dict, Any, Optional
from shared_libs.utils.exceptions import GenAIFactoryError
import asyncio

class PlanningAgent(BaseAgent):
    """
    Agent chuyên biệt chỉ tập trung vào việc tạo ra một kế hoạch hành động 
    đa bước trước khi thực thi (Plan-and-Execute Pattern).
    Nó không có Tools và không tự chạy vòng lặp thực thi.
    Vai trò: Tầng 1 (Atomic) - Cung cấp kỹ năng Lập kế hoạch.
    """
    @property
    def name(self) -> str:
        return "planning_agent"

    @property
    def description(self) -> str:
        return "Creates a detailed, step-by-step, and modular action plan for a complex user request. Focuses purely on logic and sequence, ready to be assigned to specialist agents or tools."

    def __init__(self, llm: BaseLLM):
        """Khởi tạo PlanningAgent chỉ với LLM."""
        self.llm = llm

    # --- Core Planning Method (Asynchronous) ---
    async def async_plan(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        Asynchronously generates the detailed execution plan.
        
        Args:
            user_input (str): Yêu cầu ban đầu của người dùng.
            context (Dict[str, Any], optional): Bối cảnh bổ sung (ví dụ: các chính sách, trạng thái hiện tại).

        Returns:
            str: Kế hoạch hành động chi tiết.
        """
        if context is None:
            context = {}
            
        system_message = (
            "You are an expert Strategic Planner. Your task is to analyze the 'User Request' "
            "and generate a numbered, highly detailed, and actionable plan. "
            "Each step must be a concrete action, ready to be assigned to a specialist agent or tool. "
            "The plan must be logical and comprehensive."
            "DO NOT execute the plan, just generate the steps. End your plan with the tag <PLAN_END>."
        )
        
        # Thêm bối cảnh vào prompt nếu có
        context_summary = context.get('summary', 'No additional context provided.')
        
        prompt = f"""
        USER REQUEST: {user_input}
        
        CONTEXT/POLICIES:
        ---
        {context_summary}
        ---
        
        ACTION PLAN (Start immediately with Step 1.):
        """
        
        try:
            # Dùng async_generate của LLM
            plan_output = await self.llm.async_generate(
                system_message + "\n\n" + prompt,
                temperature=0.1  # Giữ nhiệt độ thấp để có kế hoạch nhất quán và logic
            )
            return plan_output
        except Exception as e:
            raise GenAIFactoryError(f"Planning Agent failed to generate plan: {e}")

    # --- BaseAgent Abstract Methods (Enforcing Specialization) ---

    def loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        """
        Chặn phương thức loop. Planning Agent chỉ được gọi từ bên ngoài.
        """
        raise NotImplementedError("Planning Agent is managed externally by the Orchestrator and does not run a self-contained loop. Use async_plan instead.")
    
    async def async_loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        """
        Chặn phương thức async_loop.
        """
        raise NotImplementedError("Planning Agent is managed externally by the Orchestrator and does not run a self-contained loop. Use async_plan instead.")

    def plan(self, user_input: str, context: Dict[str, Any]) -> str:
        """Synchronous plan is blocked to encourage async usage."""
        raise NotImplementedError("Use the asynchronous method 'async_plan' instead for production environments.")

    def act(self, action: str, **kwargs) -> Any:
        """Planning Agent không thực hiện hành động (act)."""
        raise NotImplementedError("Planning Agent is specialized for reasoning (planning) and cannot execute actions (act).")

    def observe(self, observation: Any) -> None:
        """Planning Agent không cần cập nhật trạng thái từ quan sát."""
        pass