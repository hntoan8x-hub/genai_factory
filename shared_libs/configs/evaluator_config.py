from typing import Dict, Any, List

class EvaluatorConfig:
    """
    Configuration for various evaluation metrics.

    This class defines which evaluators to run and any specific parameters
    they require.
    """
    EVALUATION_CONFIG: Dict[str, Any] = {
        "evaluators": [
            {
                "type": "safety",
                "enabled": True,
            },
            {
                "type": "coherence",
                "enabled": True,
            },
            {
                "type": "hallucination",
                "enabled": True,
                # Additional context can be provided here, e.g., ground truth for hallucination checks
            },
        ],
    }
