from typing import Dict, Any, Union
from shared_libs.genai.base.base_tool import BaseTool
from shared_libs.genai.atomic.tools.sql_tool import SQLTool
from shared_libs.genai.atomic.tools.risk_tool import RiskTool
from shared_libs.genai.atomic.tools.web_tool import WebTool
from shared_libs.genai.atomic.tools.calculator_tool import CalculatorTool
from shared_libs.genai.atomic.tools.email_tool import EmailTool

class ToolFactory:
    """
    A factory class for creating Tool instances based on configuration.
    This class simplifies the creation of various tools used by agents.
    """

    def __init__(self):
        """Initializes the ToolFactory."""
        self._tool_types = {
            "sql": SQLTool,
            "risk": RiskTool,
            "web": WebTool,
            "calculator": CalculatorTool,
            "email": EmailTool,
        }

    def build(self, config: Dict[str, Any]) -> BaseTool:
        """
        Builds a Tool instance from a configuration dictionary.

        Args:
            config (Dict[str, Any]): A dictionary containing the tool configuration.
                                     Must have a 'type' key.

        Returns:
            BaseTool: An instance of the requested Tool type.

        Raises:
            ValueError: If the 'type' in the config is not supported.
        """
        tool_type = config.get("type")
        if not tool_type or tool_type not in self._tool_types:
            raise ValueError(f"Unsupported Tool type: {tool_type}. Supported types are: {list(self._tool_types.keys())}")
        
        tool_class = self._tool_types[tool_type]
        return tool_class()
