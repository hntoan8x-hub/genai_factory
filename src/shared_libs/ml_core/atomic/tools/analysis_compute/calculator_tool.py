from typing import Any, Dict
from pydantic import BaseModel, Field
from shared_libs.genai.base.base_tool import BaseTool

class CalculationInput(BaseModel):
    """Schema for the input of the Calculator Tool."""
    expression: str = Field(..., description="A mathematical expression to evaluate.")

class CalculationOutput(BaseModel):
    """Schema for the output of the Calculator Tool."""
    result: float = Field(..., description="The numerical result of the expression.")

class CalculatorTool(BaseTool):
    """
    A tool for performing simple mathematical calculations.

    This tool can be used by an agent to solve arithmetic problems, ensuring
    numerical accuracy in a reasoning chain.
    """

    @property
    def input_schema(self) -> BaseModel:
        return CalculationInput
    
    @property
    def output_schema(self) -> BaseModel:
        return CalculationOutput

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a mathematical expression.

        Args:
            input_data (Dict[str, Any]): The input data containing the 'expression'.

        Returns:
            Dict[str, Any]: A dictionary with the calculation result.
        """
        try:
            parsed_input = self.input_schema.model_validate(input_data)
            expression = parsed_input.expression
            
            # NOTE: Using eval() can be a security risk. For production,
            # consider using a safer library like asteval or numexpr.
            result = eval(expression)
            
            return {"result": result}
        
        except Exception as e:
            return {"result": None, "error": f"Invalid expression or calculation error: {e}"}
