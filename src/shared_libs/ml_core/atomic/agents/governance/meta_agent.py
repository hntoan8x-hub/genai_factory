# shared_libs/atomic/agents/governance/meta_agent.py

from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_llm import BaseLLM
from shared_libs.utils.exceptions import GenAIFactoryError
from typing import Dict, Any, Optional
import asyncio
import json

class MetaAgent(BaseAgent):
    """
    Agent chuyên biệt giám sát hiệu suất (latency, cost) và đề xuất/thực hiện 
    tùy chỉnh tham số (config/hyperparameters) cho các Agents khác trong hệ thống.
    Vai trò: Tầng 3 (Oversight) - Tối ưu hóa Tự động và FinOps.
    """

    @property
    def name(self) -> str:
        return "meta_optimization_agent"

    @property
    def description(self) -> str:
        return "Monitors the performance metrics (latency, token usage, error rates) of all Worker Agents and automatically recommends configuration adjustments (max_loops, temperature, LLM model) for cost and speed optimization. Responds ONLY with JSON."

    def __init__(self, llm: BaseLLM):
        """Khởi tạo MetaAgent chỉ với LLM."""
        self.llm = llm

    # --- Core Optimization Method (Asynchronous) ---
    async def async_analyze_and_propose_optimization(self, agent_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Phân tích metrics của Agent và đề xuất tùy chỉnh cấu hình.
        
        Args:
            agent_metrics (Dict): Metrics hiệu suất hiện tại (ví dụ: {'risk_manager': {'avg_cost': 0.50, 'error_rate': 0.1, 'avg_latency': 5.2}}).

        Returns:
            Dict: Đề xuất cấu hình mới (ví dụ: {'risk_manager': {'max_loops': 8, 'temperature': 0.5}}).
        """
        
        metrics_summary = "\n".join([f"- Agent {name}: {json.dumps(metrics)}" for name, metrics in agent_metrics.items()])
        
        system_message = (
            "You are the Meta-Optimization Engine. Analyze the 'Agent Performance Metrics' below. "
            "Your goal is to propose adjustments to agent configurations (e.g., max_loops, temperature, LLM model) "
            "to minimize cost, reduce latency, or lower the error rate. "
            "Respond ONLY with a valid JSON dictionary where keys are agent names and values are their new configurations."
        )

        prompt = f"""
        AGENT PERFORMANCE METRICS:
        ---
        {metrics_summary}
        ---
        
        PROPOSED OPTIMIZATION (JSON format only):
        """
        
        try:
            # LLM phân tích và trả về JSON đề xuất
            optimization_json_str = await self.llm.async_generate(
                system_message + "\n\n" + prompt,
                temperature=0.0  # Phải là deterministic để tạo ra JSON hợp lệ
            )
            
            # 🚨 HARDENING: Xử lý lỗi JSON Parsing
            try:
                # Tìm và làm sạch JSON để tránh LLM thêm văn bản ngoài lề
                # Có thể dùng regex để trích xuất { ... }
                # Tuy nhiên, ta giả định LLM tuân thủ yêu cầu "Respond ONLY with a valid JSON dictionary"
                return json.loads(optimization_json_str)
            except json.JSONDecodeError as e:
                print(f"Meta Agent: LLM returned invalid JSON. Error: {e}")
                return {} # Trả về dict rỗng nếu lỗi parse

        except Exception as e:
            raise GenAIFactoryError(f"Meta Agent failed to execute optimization task: {e}")

    # --- BaseAgent Abstract Methods (Chặn vòng lặp) ---
    def loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        raise NotImplementedError("Meta Agent is for optimization tasks, not standard loop execution.")
    
    async def async_loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        raise NotImplementedError("Meta Agent is for optimization tasks, not standard loop execution.")

    # ... (Tương tự cho plan, act, observe)