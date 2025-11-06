# shared_libs/orchestrator/pipeline_orchestrator.py (HARDENED VERSION)
import logging
from typing import Any, Dict
import asyncio
from .genai_orchestrator import GenAIOrchestrator
from shared_libs.utils.exceptions import GenAIFactoryError

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """
    Asynchronous orchestrator for a multi-stage pipeline, composing GenAI with other
    modules (NLP, CV) in sequence.
    """

    def __init__(self, genai_orchestrator: GenAIOrchestrator, nlp_module: Any = None, cv_module: Any = None):
        self.genai_orchestrator = genai_orchestrator
        self.nlp_module = nlp_module
        self.cv_module = cv_module

    async def async_run_pipeline(self, input_data: Any, session_id: str, user_role: str) -> Dict[str, Any]:
        """
        Executes the entire pipeline asynchronously. (HARDENING)
        """
        processed_data = input_data
        
        try:
            # Stage 1: Pre-processing with other modules (e.g., NLP)
            if self.nlp_module:
                logger.info("Running NLP pre-processing stage...")
                # Giả định module NLP có phương thức async_process
                processed_data = await self.nlp_module.async_process(processed_data) 
            
            # Stage 2: GenAI core processing (using the hardened GenAIOrchestrator)
            logger.info("Running GenAI core processing stage...")
            genai_result = await self.genai_orchestrator.async_run_task(processed_data, session_id, user_role)
            
            # Stage 3: Post-processing (e.g., with CV)
            if self.cv_module:
                logger.info("Running CV post-processing stage...")
                # Giả định module CV có phương thức async_enhance
                final_output = await self.cv_module.async_enhance_output(genai_result["final_output"])
                genai_result["final_output"] = final_output

            return genai_result
            
        except Exception as e:
            raise GenAIFactoryError(f"Pipeline orchestration failed at a stage: {e}")