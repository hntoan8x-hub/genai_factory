# shared_libs/atomic/agents/framework/reflexion_agent.py

from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_llm import BaseLLM
from typing import Dict, Any, Optional
from shared_libs.utils.exceptions import GenAIFactoryError
import asyncio

class ReflexionAgent(BaseAgent):
    """
    Agent chuyên biệt thực hiện Tự Phản Chiếu (Self-Reflection) trên lịch sử 
    thực thi của các Agent khác để đề xuất sửa đổi Prompt hoặc Kế hoạch.
    Nó là thành phần cốt lõi cho khả năng tự học và tăng độ bền.
    Vai trò: Tầng 1 (Atomic) - Cung cấp kỹ năng Tự Phản Chiếu.
    """
    @property
    def name(self) -> str:
        return "reflexion_agent"

    @property
    def description(self) -> str:
        return "Analyzes the execution history (including failed steps/observations) and generates an improved, corrected prompt or plan to guide the next execution cycle. Focuses on identifying and fixing errors."

    def __init__(self, llm: BaseLLM):
        """Khởi tạo ReflexionAgent chỉ với LLM."""
        self.llm = llm

    # --- Core Reflexion Method (Asynchronous) ---
    async def async_critique_and_suggest_fix(self, execution_history: str, original_task: str, current_plan: Optional[str] = None) -> str:
        """
        Asynchronously phân tích lịch sử, chỉ trích (critique) và tạo ra gợi ý sửa chữa/cải tiến.
        
        Args:
            execution_history (str): Lịch sử Thought/Act/Observe của Agent thực thi.
            original_task (str): Yêu cầu ban đầu của người dùng.
            current_plan (str, optional): Kế hoạch hiện tại đang được thực thi.

        Returns:
            str: Kết quả phân tích, bao gồm lời chỉ trích và gợi ý/chỉ dẫn tiếp theo.
        """
        
        plan_context = f"CURRENT PLAN:\n---\n{current_plan}\n---\n" if current_plan else ""

        system_message = (
            "You are a critical Meta-Learner (Reflexion Agent). Your task is to analyze the 'Execution History' of another agent. "
            "STRICTLY follow these steps:"
            "1. CRITIQUE: Analyze the history for errors (dead loops, failed tool calls, logical inconsistency, deviation from plan). If no error is found, state 'PASS'."
            "2. REVISE: If a failure is detected, provide a concrete, revised 'Next Step/Instruction' or 'Corrected Thought' that the execution agent must follow to get back on track. If passed, respond with 'None'."
            "Use the tags <CRITIQUE>...</CRITIQUE> and <REVISION>...</REVISION>."
        )
        
        prompt = f"""
        ORIGINAL TASK: {original_task}
        
        {plan_context}
        
        EXECUTION HISTORY:
        ---
        {execution_history}
        ---
        """
        
        try:
            # Dùng async_generate để thực hiện quá trình phản chiếu
            reflexion_output = await self.llm.async_generate(
                system_message + "\n\n" + prompt,
                temperature=0.2  # Nhiệt độ thấp để có tính phân tích và khách quan
            )
            return reflexion_output
        except Exception as e:
            raise GenAIFactoryError(f"Reflexion Agent failed to perform critique: {e}")

    # --- BaseAgent Abstract Methods (Enforcing Specialization) ---

    def loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        """Chặn phương thức loop. Reflexion Agent chỉ được gọi từ bên ngoài."""
        raise NotImplementedError("Reflexion Agent is managed externally by the Orchestrator and does not run a self-contained loop. Use async_critique_and_suggest_fix instead.")
    
    async def async_loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        """Chặn phương thức async_loop."""
        raise NotImplementedError("Reflexion Agent is managed externally by the Orchestrator and does not run a self-contained loop. Use async_critique_and_suggest_fix instead.")

    def plan(self, user_input: str, context: Dict[str, Any]) -> str:
        """Reflexion Agent không lập kế hoạch cho tác vụ mới."""
        raise NotImplementedError("Reflexion Agent is specialized for reflection, not initial task planning.")

    def act(self, action: str, **kwargs) -> Any:
        """Reflexion Agent không thực hiện hành động (act)."""
        raise NotImplementedError("Reflexion Agent is specialized for reasoning (reflection) and cannot execute actions (act).")

    def observe(self, observation: Any) -> None:
        """Reflexion Agent không cần cập nhật trạng thái từ quan sát."""
        pass