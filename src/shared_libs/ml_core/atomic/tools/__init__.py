"""
This module provides concrete implementations of the BaseTool interface.
These tools allow an agent to interact with external systems and data sources.
"""

from .sql_tool import SQLTool
from .risk_tool import RiskTool
from .web_tool import WebTool
from .calculator_tool import CalculatorTool
from .email_tool import EmailTool

__all__ = [
    "SQLTool",
    "RiskTool",
    "WebTool",
    "CalculatorTool",
    "EmailTool"
]
