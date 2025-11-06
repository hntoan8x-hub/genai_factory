import random
from typing import Any, Dict
from pydantic import BaseModel, Field
from shared_libs.genai.base.base_tool import BaseTool

class RiskInput(BaseModel):
    """Schema for the input of the Risk Tool."""
    customer_id: str = Field(..., description="The unique ID of the customer to assess.")
    transaction_amount: float = Field(..., description="The amount of the transaction.")

class RiskOutput(BaseModel):
    """Schema for the output of the Risk Tool."""
    risk_score: float = Field(..., ge=0.0, le=1.0, description="A risk score between 0.0 and 1.0.")
    risk_level: str = Field(..., description="Categorical risk level (low, medium, high).")
    reasoning: str = Field(..., description="The reason for the risk score.")
    
class RiskTool(BaseTool):
    """
    A tool for calling a proprietary risk assessment model.

    This tool is designed to query an external or internal model to get a risk
    score for a customer or a transaction, providing a critical data point for
    decision-making agents.
    """

    @property
    def input_schema(self) -> BaseModel:
        return RiskInput
    
    @property
    def output_schema(self) -> BaseModel:
        return RiskOutput

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls the risk model to get a score for a customer and transaction.

        Note: This is a placeholder implementation. In a production environment,
        this would make an API call to a real risk model.

        Args:
            input_data (Dict[str, Any]): The input data containing 'customer_id' and 'transaction_amount'.

        Returns:
            Dict[str, Any]: A dictionary with the risk score and related information.
        """
        try:
            parsed_input = self.input_schema.model_validate(input_data)
            customer_id = parsed_input.customer_id
            transaction_amount = parsed_input.transaction_amount
            
            print(f"Assessing risk for customer {customer_id} with transaction amount {transaction_amount}")
            
            # Simulate risk score based on amount
            if transaction_amount > 5000:
                score = random.uniform(0.7, 0.95)
                level = "high"
                reason = "High transaction amount detected."
            elif transaction_amount > 1000:
                score = random.uniform(0.4, 0.69)
                level = "medium"
                reason = "Unusual transaction amount for this customer profile."
            else:
                score = random.uniform(0.1, 0.39)
                level = "low"
                reason = "Transaction amount is within normal historical range."
            
            return {"risk_score": round(score, 2), "risk_level": level, "reasoning": reason}

        except Exception as e:
            return {"risk_score": 0.0, "risk_level": "unknown", "reasoning": f"Error during risk assessment: {e}"}
