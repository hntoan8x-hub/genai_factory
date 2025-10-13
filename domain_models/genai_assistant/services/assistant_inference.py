# domain_models/genai_assistant/services/assistant_inference.py
import logging
from typing import Any, Dict, Optional

# Import components from hardened shared_libs
from shared_libs.exceptions import SecurityError, GenAIFactoryError, LLMAPIError
# Giả định Pydantic schema cho Input đã được Hardening
from domain_models.genai_assistant.schemas.assistant_schema import AssistantInputSchema 

# Import necessary domain pipelines and services
from domain_models.genai_assistant.pipelines.safety_pipeline import SafetyPipeline
from domain_models.genai_assistant.pipelines.rag_pipeline import RAGPipeline 
from domain_models.genai_assistant.pipelines.conversation_pipeline import ConversationPipeline # Giả định pipeline này tồn tại

# Import factory for component instantiation
from shared_libs.factory.llm_factory import LLMFactory
from shared_libs.factory.tool_factory import ToolFactory
# Import configuration loader/schemas
from domain_models.genai_assistant.configs.config_loader import ConfigLoader 

logger = logging.getLogger(__name__)

class AssistantInferenceService:
    """
    The central service that orchestrates the workflow: 
    Safety Check -> Pipeline Selection -> Execution -> Output Sanitization.
    """
    
    def __init__(self):
        # 1. Load Hardened Configuration
        config_loader = ConfigLoader()
        self.assistant_config = config_loader.get_assistant_config()
        self.safety_config = config_loader.get_safety_config()
        self.llm_config = config_loader.get_llm_config() # Configuration validated by schema

        # 2. Initialize Core Shared Components
        # Assume necessary factories are initialized to provide resilient instances
        self.llm_instance = LLMFactory.create_llm(self.llm_config)
        
        # 3. Initialize Pipelines (Injecting dependencies)
        # Assume SafetyEval instance is available for SafetyPipeline
        # We use a dummy SafetyEval instance here for demonstration
        from shared_libs.atomic.evaluators.safety_eval import SafetyEval 
        safety_evaluator = SafetyEval()

        self.safety_pipeline = SafetyPipeline(self.safety_config, safety_evaluator)
        
        # Initialize business pipelines with resilient LLM/Tools
        self.rag_pipeline = RAGPipeline(
            llm=self.llm_instance, 
            retriever=ToolFactory.create_tool({"type": "retriever"}), # Example tool dependency
            config=self.assistant_config # Inject any necessary config
        ) 
        self.conversation_pipeline = ConversationPipeline(
            llm=self.llm_instance, 
            memory_service=None, # Inject memory service instance
            config=self.assistant_config
        )

    def _select_pipeline(self, request_data: AssistantInputSchema) -> Any:
        """
        Dynamically selects the appropriate pipeline based on request flags or context.
        """
        # Logic 1: Check if RAG is explicitly requested or required by context
        if getattr(request_data, 'use_rag', False): 
             logger.debug("Routing to RAG Pipeline.")
             return self.rag_pipeline

        # Logic 2: Default to the core conversation pipeline
        logger.debug("Routing to Conversation Pipeline.")
        return self.conversation_pipeline

    async def async_run_pipeline(self, request_data: AssistantInputSchema) -> Dict[str, Any]:
        """
        Main asynchronous execution flow, enforcing the Safety -> Core -> Safety pattern.
        """
        
        user_input = request_data.query
        
        # --- 1. Input Safety Check (CRITICAL HARDENING) ---
        # The safety pipeline raises SecurityError on failure, which is caught by assistant_service.py
        await self.safety_pipeline.check_input(user_input) 
        logger.info("Input passed all safety and injection checks.")
        
        llm_output = ""
        try:
            # --- 2. Core Inference Execution ---
            selected_pipeline = self._select_pipeline(request_data)
            
            # Execute the pipeline using its asynchronous run method
            llm_output = await selected_pipeline.async_run(user_input, request_data.context)
            
        except LLMAPIError as e:
            # Catch LLM errors (even after retries/fallback failed)
            logger.error(f"LLM API failure during inference: {e}")
            raise GenAIFactoryError(f"LLM backend failed during execution.") from e
            
        except GenAIFactoryError as e:
            # Catch other internal framework errors (Tool execution, etc.)
            logger.error(f"Pipeline execution failed: {e}")
            raise # Re-raise for assistant_service.py to handle the 503 response

        # --- 3. Output Safety Check and Sanitization (CRITICAL HARDENING) ---
        # Output check handles toxicity and redacts PII, returning a sanitized string.
        final_output = await self.safety_pipeline.check_output(llm_output)
        
        logger.info("Output passed moderation and sanitization.")
        
        # Log final interaction (Interaction Logger should be called here)
        # self.interaction_logger.log_interaction(...)

        return {"response": final_output, "status": "success"}