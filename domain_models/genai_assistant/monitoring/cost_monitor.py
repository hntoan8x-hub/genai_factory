from typing import Dict, Any

class CostMonitor:
    """
    Monitors token usage and calculates API costs.
    
    This monitor tracks input and output tokens for LLM calls and
    provides a running total of estimated costs.
    """

    def __init__(self):
        """Initializes storage for cost metrics."""
        self.metrics: Dict[str, Dict[str, float]] = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "estimated_cost": 0.0
        }
        # Simplified token pricing
        self.cost_per_token = {
            "gpt-4": {"input": 0.00003, "output": 0.00006},
            "claude-3": {"input": 0.000015, "output": 0.000075},
        }

    def record_usage(self, model_name: str, input_tokens: int, output_tokens: int):
        """
        Records token usage and updates the estimated cost.
        
        Args:
            model_name (str): The name of the LLM model used.
            input_tokens (int): The number of tokens in the prompt.
            output_tokens (int): The number of tokens in the response.
        """
        self.metrics["total_input_tokens"] += input_tokens
        self.metrics["total_output_tokens"] += output_tokens
        
        pricing = self.cost_per_token.get(model_name)
        if pricing:
            input_cost = input_tokens * pricing["input"]
            output_cost = output_tokens * pricing["output"]
            self.metrics["estimated_cost"] += input_cost + output_cost

    def get_report(self) -> Dict[str, float]:
        """Returns the current cost report."""
        return self.metrics
