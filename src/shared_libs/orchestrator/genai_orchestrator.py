# shared_libs/orchestrator/genai_orchestrator.py (HARDENED VERSION)
import logging
from typing import Any, Dict, List
import asyncio
from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_memory import BaseMemory
from shared_libs.base.base_evaluator import BaseEvaluator
from shared_libs.utils.exceptions import GenAIFactoryError 
# Giả định đã có TracingUtils và LatencyMonitor
from shared_libs.utils.tracing_utils import TracingUtils 
from src.shared_libs.monitoring.utils.latency_monitor import LatencyMonitor 

logger = logging.getLogger(__name__)

class GenAIOrchestrator:
    """
    The central asynchronous orchestrator for a single GenAI agentic loop.
    Manages the task lifecycle, coordinating the agent, memory, tracing, and evaluation.
    """

    def __init__(
        self,
        agent: BaseAgent,
        memory: BaseMemory,
        evaluators: List[BaseEvaluator] = None,
        latency_monitor: LatencyMonitor = None, # HARDENING: Inject Monitor
    ):
        self.agent = agent
        self.memory = memory
        self.evaluators = evaluators if evaluators else []
        self.latency_monitor = latency_monitor

    async def async_run_task(self, query: str, session_id: str, user_role: str) -> Dict[str, Any]:
        """
        Executes a task asynchronously, enclosing the entire lifecycle within a trace span and timer.
        """
        final_output = None
        evaluation_results = {}
        
        # HARDENING 1: Start a centralized Trace Span for the entire task (CRITICAL)
        async with TracingUtils.async_span("genai_full_task", "orchestration", {"session_id": session_id, "agent_name": self.agent.name}) as span: #
            
            # HARDENING 2: Measure overall task latency (FinOps/SLA Monitoring)
            # Giả định self.agent có thuộc tính llm.model_name
            async with LatencyMonitor.Timer(self.latency_monitor, "genai_full_task", self.agent.llm.model_name, session_id): #
                try:
                    # 1. Retrieve prior context (Should ideally be traced by MemoryService itself)
                    context = await self.memory.async_retrieve(session_id) 
                    
                    # 2. Execute the core agentic loop
                    final_output = await self.agent.async_loop(query, context=context)
                    
                    # 3. Store the final conversation/output
                    await self.memory.async_store(session_id, {"query": query, "response": final_output})

                    # 4. Run asynchronous evaluation
                    evaluation_results = await self._async_run_evaluators(query, final_output)
                    
                    span.set_attribute("status", "SUCCESS") #

                    return {
                        "final_output": final_output,
                        "evaluations": evaluation_results
                    }

                except asyncio.TimeoutError:
                    span.set_attribute("status", "TIMEOUT")
                    raise GenAIFactoryError("Agent task timed out during execution.")
                except Exception as e:
                    span.set_attribute("status", "FAILED") #
                    raise GenAIFactoryError(f"An error occurred during orchestration: {e}")

    async def _async_run_evaluators(self, input_data: str, output: str) -> Dict[str, Any]:
        """
        Executes all configured evaluators on the agent's output asynchronously.
        """
        results = {}
        # Run evaluators concurrently for speed
        tasks = []
        for evaluator in self.evaluators:
            tasks.append(evaluator.async_evaluate(input_data=input_data, output=output, context={}))
        
        # HARDENING: Use asyncio.gather to run tasks in parallel
        eval_results_list = await asyncio.gather(*tasks, return_exceptions=True) 

        for evaluator, result in zip(self.evaluators, eval_results_list):
            eval_name = evaluator.__class__.__name__
            if isinstance(result, Exception):
                logger.error(f"Error running async evaluator '{eval_name}': {result}")
                results[eval_name] = {"error": str(result)}
            else:
                results[eval_name] = result
        
        return results