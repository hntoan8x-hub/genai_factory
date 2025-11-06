# GenAI_Factory/src/domain_models/genai_assistant/pipelines/2_agent_orchestration/orchestration_pipeline.py

import logging
import asyncio
from typing import Dict, Any, List
from shared_libs.factory.agent_factory import AgentFactory
from shared_libs.base.base_tool import BaseTool
from shared_libs.base.base_agent import BaseAgent # Giả định BaseAgent có async_run
from shared_libs.utils.exceptions import GenAIFactoryError, ToolExecutionError
from domain_models.genai_assistant.services.tool_service import ToolService # CRITICAL HARDENING
from src.shared_libs.telemetry.telemetry_logger import get_tracer # Tracing
from src.shared_libs.monitoring.utils.latency_monitor import LatencyMonitor # Monitoring

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)

class OrchestrationPipeline:
    """
    Orchestrates complex tasks using a multi-agent system.
    This pipeline selects and runs the appropriate agent to fulfill a user's request
    while ensuring security via ToolService and performance monitoring. (HARDENING)
    """

    def __init__(self, agent_config: Dict[str, Any], tool_service: ToolService, latency_monitor: LatencyMonitor):
        """
        Initializes the OrchestrationPipeline.

        Args:
            agent_config (Dict[str, Any]): Configuration for the Agent (LLM, tool selection).
            tool_service (ToolService): Hardened service for secure tool access.
            latency_monitor (LatencyMonitor): Service for tracking performance metrics.
        """
        self.agent_config = agent_config
        self.tool_service = tool_service
        self.latency_monitor = latency_monitor
        
        # 1. Khởi tạo Agent
        # AgentFactory sẽ tạo Agent (ví dụ: ReAct, CrewAI) và truyền vào tool_service 
        # để Agent sử dụng ToolService thay vì gọi Tool trực tiếp.
        self.agent: BaseAgent = self._setup_agent()
        
        logger.info(f"OrchestrationPipeline initialized. Agent: {self.agent.__class__.__name__}")

    def _setup_agent(self) -> BaseAgent:
        """Instantiates the core agent based on configuration."""
        # Giả định AgentFactory nhận ToolService để inject vào Agent
        try:
            return AgentFactory.build(
                config=self.agent_config, 
                tool_service=self.tool_service # Agent phải dùng ToolService này
            )
        except Exception as e:
            logger.critical(f"FATAL: Failed to initialize Agent: {e}")
            raise GenAIFactoryError(f"Agent initialization failed.") from e

    async def async_run(self, query: str, user_role: str) -> Dict[str, Any]:
        """
        Executes the orchestration pipeline asynchronously and tracks performance.
        
        Args:
            query (str): The user's input query.
            user_role (str): The role of the user (e.g., 'admin', 'guest') for ToolService access control.
            
        Returns:
            Dict[str, Any]: The final output from the agent's execution.
        """
        model_name = self.agent_config.get("llm", {}).get("model_name", "orchestration_model")
        
        # 1. Tracing Start (CRITICAL GOVERNANCE)
        with tracer.start_as_current_span("OrchestrationPipeline.async_run") as span:
            span.set_attribute("user.role", user_role)
            span.set_attribute("agent.type", self.agent.__class__.__name__)
            
            # 2. Latency Monitoring Start (CRITICAL PERFORMANCE MONITORING)
            async with self.latency_monitor.Timer(
                monitor=self.latency_monitor, 
                operation_name="agent_orchestration", 
                model_name=model_name, 
                session_id=span.context.span_id # Sử dụng Span ID làm Session ID
            ):
                logger.info(f"Executing Agent '{self.agent.__class__.__name__}' for user role '{user_role}'.")
                
                try:
                    # 3. Agent Execution (Bất đồng bộ)
                    # Agent's async_run() sẽ tự động gọi ToolService.async_execute_tool() bên trong
                    result = await self.agent.async_run(query=query, user_role=user_role)
                    
                    # 4. Chuẩn hóa kết quả
                    return {
                        "response": result.get("final_answer", result.get("output", "Agent completed without a clear final answer.")),
                        "metadata": {
                            "agent_type": self.agent.__class__.__name__,
                            "steps_taken": result.get("steps", []),
                            "model": model_name,
                        },
                        "pipeline": "orchestration_pipeline"
                    }
                    
                except ToolExecutionError as e:
                    # Lỗi thực thi Tool (ví dụ: Tool API trả về lỗi)
                    logger.error(f"Agent failed due to Tool execution error: {e}")
                    raise GenAIFactoryError(f"Agent execution failed: Tool error. {e}") from e

                except Exception as e:
                    # Lỗi không xác định khác trong quy trình Agent
                    logger.critical(f"Unhandled critical error during Agent execution: {e}")
                    raise GenAIFactoryError("Agent encountered a critical internal error.") from e