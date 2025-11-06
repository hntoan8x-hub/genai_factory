# GenAI_Factory/src/domain_models/genai_assistant/pipelines/3_internal_utility/safety_pipeline.py

import logging
from typing import Any, Dict
from domain_models.genai_assistant.schemas.config_schemas import SafetyConfigSchema
from shared_libs.atomic.evaluators.safety_eval import SafetyEval 
from shared_libs.utils.exceptions import SecurityError, GenAIFactoryError 
import re 

logger = logging.getLogger(__name__)

class SafetyPipeline:
    """
    Implements a multi-layered safety check pipeline using validated configuration (Defense-in-Depth).
    This serves as the critical security Quality Gate for both input and output.
    """

    def __init__(self, safety_config: SafetyConfigSchema, safety_evaluator: SafetyEval):
        """
        Initializes the pipeline with the validated safety configuration and the evaluator.
        
        Args:
            safety_config: The Pydantic SafetyConfigSchema instance (validated).
            safety_evaluator: The Base SafetyEval instance for content moderation checks.
        """
        self.config = safety_config
        self.safety_evaluator = safety_evaluator
        
        # Biên dịch PII patterns ngay khi khởi tạo để tối ưu hiệu suất runtime (Hardening)
        self.compiled_pii_patterns = []
        for pattern_str in self.config.pii_patterns:
            try:
                self.compiled_pii_patterns.append(re.compile(pattern_str, re.IGNORECASE))
            except re.error as e:
                logger.error(f"Invalid regex pattern in SafetyConfig: {pattern_str}. Error: {e}")
                # Không thêm pattern lỗi vào danh sách thực thi
                continue 

    async def check_input(self, user_input: str) -> bool:
        """
        Runs input safety and injection checks based on validated configuration.
        Returns True if safe, raises SecurityError if blocked (CRITICAL BLOCK).
        """
        logger.info("Starting input safety checks.")

        # --- 1. Prompt Injection Check (Hardening against Agent Misuse) ---
        if self.config.input_injection_check:
            # Kiểm tra Blocklist từ Schema
            if any(banned_word in user_input.lower() for banned_word in self.config.blocklist):
                 logger.warning("Input blocked: Detected forbidden keyword.")
                 raise SecurityError("Input blocked: Potential prompt injection or forbidden keywords detected.")

        # --- 2. Input Content Moderation ---
        try:
            eval_result = await self.safety_evaluator.async_evaluate(
                input_data=user_input, 
                output=user_input, 
                context={"mode": "input"}
            )
            toxicity_score = eval_result.get('score', 0.0)
        except Exception as e:
            logger.error(f"Safety Evaluator failed during input check: {e}")
            # Decision: Nếu Safety Evaluator lỗi, ta nên chặn request theo nguyên tắc an toàn
            raise SecurityError("Input check failed due to technical error in moderation system.")

        if toxicity_score < self.config.toxicity_threshold:
            logger.warning(f"Input failed toxicity check. Score: {toxicity_score}. Threshold: {self.config.toxicity_threshold}")
            raise SecurityError(f"Input blocked: Fails toxicity threshold.")

        return True 

    async def check_output(self, llm_output: str) -> str:
        """
        Runs output safety checks and performs PII redaction.
        Returns the sanitized output or a default safe message.
        """
        logger.info("Starting output safety checks.")
        redacted_output = llm_output

        # --- 1. Output Content Moderation ---
        try:
            eval_result = await self.safety_evaluator.async_evaluate(
                input_data="", 
                output=llm_output, 
                context={"mode": "output"}
            )
            toxicity_score = eval_result.get('score', 0.0)
        except Exception as e:
            logger.error(f"Safety Evaluator failed during output check: {e}")
            # Hardening: Nếu hệ thống đánh giá lỗi, ta trả về thông báo an toàn mặc định
            return "A safety system error occurred. Cannot provide the generated response."

        if toxicity_score < self.config.toxicity_threshold:
            logger.critical(f"Output failed toxicity check. Score: {toxicity_score}.")

            # XỬ LÝ DỰA TRÊN CẤU HÌNH output_toxicity_action (CRITICAL HARDENING)
            if self.config.output_toxicity_action.upper() == "BLOCK":
                 # Chặn cứng - AssistantService sẽ chuyển đổi thành 403
                 raise SecurityError("Output blocked due to high toxicity (Configured to BLOCK).")
            
            # Mặc định (REDACT): Trả về phản hồi an toàn
            return "I cannot provide a response that violates safety guidelines. Please rephrase your request."

        # --- 2. PII Redaction (Hardening against Data Leakage) ---
        
        if self.compiled_pii_patterns:
            for pattern in self.compiled_pii_patterns: 
                redacted_output = pattern.sub("[REDACTED]", redacted_output)
            
            if redacted_output != llm_output:
                 logger.info("PII found and redacted in output.")
            
            return redacted_output

        return llm_output