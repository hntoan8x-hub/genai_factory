# shared_libs/atomic/agents/governance/supervisor_agent.py

from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_llm import BaseLLM
from shared_libs.atomic.agents.framework.planning_agent import PlanningAgent
from shared_libs.atomic.agents.framework.reflexion_agent import ReflexionAgent
from shared_libs.utils.exceptions import GenAIFactoryError
from typing import Dict, Any, List, Optional
import asyncio

class SupervisorAgent(BaseAgent):
    """
    Agent chuyên biệt quản lý luồng làm việc (Work Flow Orchestration). 
    Nó điều phối các bước, phân công nhiệm vụ, và quản lý các Agent Worker.
    Vai trò: Tầng 3 (Manager/Supervisor).
    """

    @property
    def name(self) -> str:
        return "workflow_supervisor_agent"

    @property
    def description(self) -> str:
        return "Manages complex multi-step workflows. It uses a Planning Agent to define steps and orchestrates execution by assigning tasks to specialized Worker Agents."

    def __init__(self, llm: BaseLLM, worker_agents: Dict[str, BaseAgent]):
        """
        Khởi tạo Supervisor.
        
        Args:
            llm (BaseLLM): LLM để ra quyết định điều phối.
            worker_agents (Dict): Từ điển chứa các Worker Agent (Tầng 2) được Factory cung cấp.
        """
        self.llm = llm
        self.worker_agents = worker_agents
        
        # Khởi tạo các Framework Agent cần thiết (Internal Skills)
        self.planner = PlanningAgent(llm)
        self.reflector = ReflexionAgent(llm)
        self.task_history: List[str] = []

    # --- Core Orchestration Method (Asynchronous) ---
    async def run_task(self, user_input: str, max_orchestration_steps: int = 20) -> str:
        """
        Chạy toàn bộ luồng làm việc, bao gồm lập kế hoạch, thực thi và tự sửa lỗi.
        """
        self.task_history = []
        
        # 1. Lập kế hoạch (Gọi Planning Agent - Tầng 1)
        self.task_history.append("STEP 1: Calling Planning Agent to generate workflow plan.")
        try:
            plan = await self.planner.async_plan(user_input)
            self.task_history.append(f"PLAN GENERATED:\n{plan}")
        except GenAIFactoryError as e:
            return f"Orchestration Failed during Planning: {e}"

        # 2. Điều phối Thực thi (Execution Loop)
        current_step = 1
        final_result = None
        
        # NOTE: Logic phân tích Plan và giao nhiệm vụ cho Workers (Tầng 2) sẽ là phức tạp nhất
        # Trong ví dụ này, chúng ta sẽ mô phỏng việc giao việc và kiểm tra kết quả.

        while current_step <= max_orchestration_steps:
            # Mô phỏng: Supervisor quyết định Agent nào cần thực hiện bước tiếp theo
            
            # (Phần này sẽ được thay thế bằng LLM call để ra quyết định thực tế)
            # decision_prompt = self._create_decision_prompt(plan, current_step, self.task_history)
            # decision = await self.llm.async_generate(decision_prompt)
            # chosen_agent, task = self._parse_decision(decision)
            
            # --- Logic Mô phỏng Quyết định Điều phối đơn giản ---
            if current_step == 1:
                chosen_agent = self.worker_agents.get("risk_manager")
                task = f"Execute initial risk analysis for the request: {user_input}"
            elif current_step == 2 and "risk_manager" in self.worker_agents:
                # Giả sử cần gọi Critic sau bước thực thi
                chosen_agent = self.worker_agents.get("compliance_critic")
                task = "Review the Risk Manager's output."
            else:
                final_result = "Orchestration completed based on simplified flow."
                break
            # ----------------------------------------------------
            
            if chosen_agent is None:
                self.task_history.append(f"Error: Required Agent not available for step {current_step}. Aborting.")
                break
                
            self.task_history.append(f"STEP {current_step}: Assigning task to {chosen_agent.name}: '{task}'")
            
            try:
                # 3. Thực thi (Gọi Agent Worker - Tầng 2)
                # Giả định Worker Agent có một method run_task_fragment
                if hasattr(chosen_agent, 'run_task_fragment'):
                    result = await chosen_agent.run_task_fragment(task)
                elif hasattr(chosen_agent, 'async_review'): # Dành cho Critic
                    result = await chosen_agent.async_review("Mock final answer from Risk Manager", {}, "Mock Policies")
                else:
                    result = chosen_agent.loop(task) # Dùng loop nếu Worker là ReActAgent
                
                self.task_history.append(f"RESULT from {chosen_agent.name}: {result}")
                
                # 4. Tự sửa lỗi (Gọi Reflexion Agent - Tầng 1)
                if self._needs_reflection(result):
                    critique = await self.reflector.async_critique_and_suggest_fix("\n".join(self.task_history), user_input, plan)
                    self.task_history.append(f"REFLEXION: {critique}")
                    # Logic để điều chỉnh Plan hoặc History dựa trên critique sẽ được thêm vào đây
                    
                current_step += 1

            except Exception as e:
                self.task_history.append(f"Execution failed at step {current_step} with error: {e}")
                
                # Cơ chế thoát khẩn cấp sau lỗi
                return "\n".join(self.task_history) + f"\n\nFINAL STATUS: FAILED due to execution error."
                
        return final_result if final_result else "\n".join(self.task_history) + "\n\nFINAL STATUS: UNKNOWN (Max steps reached)."
        
    # --- Helper Method (Mô phỏng kiểm tra lỗi) ---
    def _needs_reflection(self, result: Any) -> bool:
        """Kiểm tra xem kết quả có lỗi hoặc cần phản chiếu không."""
        return "Error" in str(result) or "FAIL" in str(result)
    
    # --- BaseAgent Abstract Methods (Enforcing Specialization) ---

    # SupervisorAgent chứa logic loop phức tạp (run_task) nhưng được gọi từ bên ngoài
    def loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        raise NotImplementedError("Supervisor Agent runs the complex 'run_task' orchestration, not a simple ReAct loop.")
    
    async def async_loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        # Nếu muốn sử dụng run_task theo hợp đồng async_loop
        return await self.run_task(user_input, max_orchestration_steps=max_steps)

    def plan(self, user_input: str, context: Dict[str, Any]) -> str:
        raise NotImplementedError("Supervisor delegates planning to PlanningAgent.")

    def act(self, action: str, **kwargs) -> Any:
        raise NotImplementedError("Supervisor delegates execution to Worker Agents.")

    def observe(self, observation: Any) -> None:
        pass # Trạng thái được quản lý thông qua task_history