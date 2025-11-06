# GenAI_Factory/src/domain_models/genai_assistant/services/assistant_inference.py

import logging
from typing import Any, Dict, Optional
import time 
# Import components from hardened shared_libs
from shared_libs.utils.exceptions import SecurityError, GenAIFactoryError, LLMAPIError
from shared_libs.factory.llm_factory import LLMFactory
from shared_libs.factory.tool_factory import ToolFactory
from shared_libs.base.base_llm import BaseLLM

# 🚨 CẬP NHẬT: Import BaseTracker để theo dõi MLOps
from shared_libs.mlops.base.base_tracker import BaseTracker

# Import hardened domain schemas and pipelines
from domain_models.genai_assistant.schemas.assistant_schema import AssistantInputSchema 
from domain_models.genai_assistant.schemas.config_schemas import LLMConfigSchema, SafetyConfigSchema
from domain_models.genai_assistant.pipelines.safety_pipeline import SafetyPipeline
from domain_models.genai_assistant.pipelines.rag_pipeline import RAGPipeline 
from domain_models.genai_assistant.pipelines.conversation_pipeline import ConversationPipeline 
from domain_models.genai_assistant.pipelines.orchestration_pipeline import OrchestrationPipeline 
from domain_models.genai_assistant.services.memory_service import MemoryService 
from domain_models.genai_assistant.services.tool_service import ToolService 
from src.domain_models.genai_assistant.utils.interaction_logger import log_interaction # Logging

logger = logging.getLogger(__name__)

class AssistantInferenceService:
    """
    The central service that orchestrates the workflow: 
    Safety Check -> Pipeline Selection -> Execution -> Output Sanitization.
    It is the core execution unit of the GenAI Assistant API.
    """
    
    # 🚨 CẬP NHẬT: Thêm tracker: Optional[BaseTracker] vào __init__
    def __init__(self, configs: Dict[str, Any], memory_service: MemoryService, tool_service: ToolService, tracker: Optional[BaseTracker] = None):
        """
        Initializes the service by injecting validated configurations and hardened components.
        """
        # Load Hardened Configuration Schemas
        self.llm_config: LLMConfigSchema = configs['llm_config']
        self.safety_config: SafetyConfigSchema = configs['safety_config']
        self.assistant_config: Dict[str, Any] = configs['assistant_config']

        # Hardened Dependencies
        self.memory_service = memory_service
        self.tool_service = tool_service
        self.tracker = tracker # Lưu BaseTracker

        # 1. Initialize Core Shared Components (Resilient LLM)
        self.llm_instance: BaseLLM = LLMFactory.build(self.llm_config.dict())
        
        # 2. Initialize Safety Pipeline (CRITICAL HARDENING)
        from shared_libs.atomic.evaluators.safety_eval import SafetyEval 
        safety_evaluator = SafetyEval() # Assuming atomic evaluator is ready
        self.safety_pipeline = SafetyPipeline(self.safety_config, safety_evaluator)
        
        # 3. Initialize Business Pipelines (Injecting dependencies)
        self.pipelines: Dict[str, Any] = self._initialize_pipelines()

    def _initialize_pipelines(self) -> Dict[str, Any]:
        """Initializes all domain-specific pipelines with their hardened dependencies."""
        
        # RAG Pipeline (Cần LLM và Retriever Config/Tool)
        rag_pipeline = RAGPipeline(
            llm_config=self.llm_config, 
            retriever_config=self.assistant_config['retriever_config'], # Giả định RetrieverConfigSchema được inject
            rag_prompt_config=self.assistant_config.get('rag_prompt', {})
        ) 
        
        # Conversation Pipeline (Cần LLM và Memory Service)
        conversation_pipeline = ConversationPipeline(
            config=self.assistant_config, 
            llm_instance=self.llm_instance, 
            memory_service=self.memory_service
        )
        
        # Orchestration Pipeline (Cần LLM Config, Tool Service)
        orchestration_pipeline = OrchestrationPipeline(
            agent_config=self.assistant_config.get('agent_config', {}), 
            tool_service=self.tool_service, 
            latency_monitor=None # Giả định LatencyMonitor được inject ở AssistantService
        )
        
        return {
            "conversation": conversation_pipeline,
            "rag": rag_pipeline,
            "orchestration": orchestration_pipeline
        }


    def _select_pipeline(self, pipeline_type: str) -> Any:
        """
        Dynamically selects the appropriate pipeline based on type.
        Raises an error if the pipeline is not configured.
        """
        pipeline = self.pipelines.get(pipeline_type)
        if not pipeline:
            logger.warning(f"Requested pipeline type '{pipeline_type}' not found.")
            raise GenAIFactoryError(f"Pipeline type '{pipeline_type}' not supported.")
        return pipeline

    async def async_run_pipeline(self, request_data: AssistantInputSchema, user_role: str) -> Dict[str, Any]:
        """
        Main asynchronous execution flow, enforcing the Safety -> Core -> Safety pattern.
        """
        start_time = time.time()
        user_input = request_data.query
        
        # --- 1. Input Safety Check (CRITICAL HARDENING: First Gate) ---
        # Raises SecurityError on failure, which is caught by assistant_service.py
        await self.safety_pipeline.check_input(user_input) 
        logger.info("Input passed all safety and injection checks.")
        
        llm_output = ""
        pipeline_name = request_data.pipeline_type
        
        try:
            # --- 2. Core Inference Execution ---
            selected_pipeline = self._select_pipeline(pipeline_name)
            
            # Kiểm tra xem pipeline có cần user_role không (ví dụ: orchestration)
            if hasattr(selected_pipeline, 'async_run_with_role'):
                raw_response_data = await selected_pipeline.async_run_with_role(user_input, user_role)
            else:
                # Execution cho conversation/rag
                raw_response_data = await selected_pipeline.async_run(request_data.user_id, user_input)
            
            llm_output = raw_response_data.get("response", "")
            
        except GenAIFactoryError as e:
            # Catch internal framework errors (LLM Fallback/Retry failed, Tool execution failed)
            logger.error(f"Pipeline execution failed: {e.__class__.__name__}")
            raise # Re-raise for assistant_service.py to handle the 503 response

        # --- 3. Output Safety Check and Sanitization (CRITICAL HARDENING: Final Gate) ---
        # Output check handles toxicity and redacts PII, returning a sanitized string.
        final_output = await self.safety_pipeline.check_output(llm_output)
        logger.info("Output passed moderation and sanitization.")
        
        duration = time.time() - start_time
        
        # 4. Log final interaction (Hardening: Data Collection for Retraining/Audit)
        log_interaction(request_data.user_id, request_data.dict(), {"response": final_output, "pipeline": pipeline_name})

        # 5. Prepare Output for AssistantService (Metadata for Audit)
        # Giả định có thể tính toán chi phí và token ở đây
        tokens_input = len(user_input.split())
        tokens_output = len(final_output.split())
        cost_usd = 0.0001 * tokens_output # Chi phí ước tính

        # 🚨 CẬP NHẬT: Thêm logic MLflow Inference Tracking
        self._log_inference_metrics(request_data.user_id, pipeline_name, duration, cost_usd, tokens_input, tokens_output)
        
        return {
            "response": final_output, 
            "pipeline": pipeline_name,
            "metadata": raw_response_data.get("metadata", {}),
            "llm_cost_usd": cost_usd,
            "tokens_used": {"input": tokens_input, "output": tokens_output}
        }

    # 🚨 CẬP NHẬT: Thêm phương thức hỗ trợ cho việc log MLflow
    def _log_inference_metrics(self, user_id: str, pipeline_name: str, duration: float, cost_usd: float, tokens_input: int, tokens_output: int) -> None:
        """
        Logs inference metadata and metrics using the injected BaseTracker.
        This assumes the BaseTracker can log metrics without explicit start_run/end_run
        for a quick, stateless logging of inference calls.
        """
        if not self.tracker:
            logger.debug("MLflow Tracker not initialized for inference. Skipping logging.")
            return

        try:
            # Log Parameters (Context)
            # Dùng tags hoặc param cho các trường có cardinality cao như user_id
            self.tracker.log_param("user_id", user_id) 
            self.tracker.log_param("pipeline_type_used", pipeline_name)
            
            # Log Metrics (Performance & Cost)
            metrics = {
                "inference_latency_sec": duration,
                "llm_cost_usd": cost_usd,
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "total_tokens": tokens_input + tokens_output,
            }
            self.tracker.log_metrics(metrics)
            
            logger.debug(f"MLflow inference tracked for user {user_id}. Duration: {duration:.4f}s")

        except Exception as e:
            # Ghi lại lỗi nhưng không chặn luồng chính
            logger.error(f"Failed to log inference metrics to tracker: {e.__class__.__name__}", exc_info=True)