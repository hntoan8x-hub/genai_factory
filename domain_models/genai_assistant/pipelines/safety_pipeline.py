# domain_models/genai_assistant/pipelines/safety_pipeline.py
import logging
from typing import Any, Dict
from domain_models.genai_assistant.configs.config_loader import ConfigLoader 
from domain_models.genai_assistant.schemas.config_schemas import SafetyConfigSchema
from shared_libs.atomic.evaluators.safety_eval import SafetyEval 
from shared_libs.exceptions import SecurityError

logger = logging.getLogger(__name__)

class SafetyPipeline:
    """
    Implements a multi-layered safety check pipeline for both input and output.
    This pipeline uses a Defense-in-Depth strategy.
    """

    def __init__(self, safety_config: SafetyConfigSchema, safety_evaluator: SafetyEval):
        """
        Initializes the pipeline with the validated safety configuration and the evaluator.
        """
        self.config = safety_config
        self.safety_evaluator = safety_evaluator

    async def check_input(self, user_input: str) -> bool:
        """
        Runs input safety and injection checks.
        Returns True if safe, raises SecurityError if blocked.
        """
        logger.info("Starting input safety checks.")

        # --- 1. Prompt Injection Check (HARDENING) ---
        if self.config.input_injection_check:
            # Simplified Check: In production, this would use a dedicated PI model or sophisticated heuristics.
            if any(banned_word in user_input.lower() for banned_word in self.config.blocklist):
                 logger.warning("Input blocked by blocklist/injection heuristic.")
                 raise SecurityError("Input blocked: Detected potential prompt injection or forbidden keywords.")

        # --- 2. Input Content Moderation ---
        # Run the Safety Evaluator asynchronously on the input
        eval_result = await self.safety_evaluator.async_evaluate(
            input_data=user_input, 
            output=user_input, 
            context={"mode": "input"}
        )

        if eval_result['score'] < self.config.toxicity_threshold:
            logger.warning(f"Input failed toxicity check. Score: {eval_result['score']}. Flags: {eval_result['flags']}")
            raise SecurityError(f"Input blocked: Fails toxicity threshold.")

        return True # Input is safe

    async def check_output(self, llm_output: str) -> str:
        """
        Runs output safety checks and performs PII redaction.
        Returns the sanitized output.
        """
        logger.info("Starting output safety checks.")

        # --- 1. Output Content Moderation ---
        eval_result = await self.safety_evaluator.async_evaluate(
            input_data="", 
            output=llm_output, 
            context={"mode": "output"}
        )

        if eval_result['score'] < self.config.toxicity_threshold:
            logger.critical(f"Output failed toxicity check. Score: {eval_result['score']}. Blocked/Redacted.")
            # **HARDENING**: Instead of raising error, we return a safe, pre-defined response.
            return "I cannot provide a response that violates safety guidelines. Please rephrase your request."

        # --- 2. PII Redaction (HARDENING) ---
        # Simplified: Replace all phone numbers with [REDACTED]
        if "Sensitive information" in eval_result['flags']:
            import re
            # Dùng regex đã định nghĩa trong SafetyEval
            for pattern in self.safety_evaluator.SENSITIVE_PATTERNS: 
                llm_output = re.sub(pattern, "[REDACTED]", llm_output)
            logger.info("PII (Sensitive Info) found and redacted in output.")

        return llm_output