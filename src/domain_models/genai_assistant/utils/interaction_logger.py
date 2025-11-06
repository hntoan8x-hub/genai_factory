# domain_models/genai_assistant/logging/interaction_logger.py (CỦNG CỐ)

import json
import logging
import time
from typing import Dict, Any
# Import Schema đã được Hardening (Giả định được sử dụng bên ngoài)
from domain_models.genai_assistant.schemas.assistant_schema import AssistantOutputSchema, AssistantInputSchema 

# Set up a dedicated logger for user interactions
interaction_logger = logging.getLogger("interaction_logger")

def log_interaction(request_id: str, user_id: str, input_data: Dict[str, Any], output_data: Dict[str, Any]):
    """
    Logs a single user-assistant interaction in a structured JSON format 
    for MLOps Retraining and Quality Assessment.
    """
    # LƯU Ý: Dữ liệu output_data phải là dữ liệu đã được SafetyPipeline xử lý (redacted).
    
    log_entry = {
        "timestamp": time.time(),
        "request_id": request_id, # Key để liên kết với Audit/Telemetry
        "user_id": user_id,
        "input": input_data,
        "output": output_data,
        "pipeline_used": output_data.get("pipeline"),
        "cost_usd": output_data.get("llm_cost_usd", 0.0)
    }
    # Ghi log dưới dạng JSON String
    interaction_logger.info(json.dumps(log_entry))