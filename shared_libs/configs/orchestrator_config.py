from typing import Dict, Any, List

class OrchestratorConfig:
    """
    High-level configuration for the orchestrator components.

    This class defines global settings like maximum loops, logging options,
    and which evaluators to use for a given pipeline.
    """
    GENAI_ORCHESTRATOR_CONFIG: Dict[str, Any] = {
        "agent_type": "react",
        "memory_enabled": True,
        "evaluators": ["safety", "coherence"], # List of evaluator keys to use
    }
    
    PIPELINE_ORCHESTRATOR_CONFIG: Dict[str, Any] = {
        "steps": [
            {"module": "nlp", "config": {"type": "text_processor"}},
            {"module": "genai", "config": GENAI_ORCHESTRATOR_CONFIG},
            {"module": "cv", "config": {"type": "image_enhancer"}},
        ],
        "logging_level": "INFO",
    }
