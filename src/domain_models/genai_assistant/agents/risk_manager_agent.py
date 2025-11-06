# # domain_models/genai_assistant/agents/risk_manager_agent.py

from src.shared_libs.atomic.agents.framework.react_agent import ReActAgent
from shared_libs.base.base_llm import BaseLLM
from typing import List
from shared_libs.base.base_tool import BaseTool

class RiskManagerAgent(ReActAgent):
    """
    A specialized ReAct Agent that acts as the Lead Analyst, responsible for
    executing a complex risk analysis task by orchestrating tools.
    """
    
    @property
    def name(self) -> str:
        return "financial_risk_manager_agent"

    @property
    def description(self) -> str:
        return (
            "You are a Senior Financial Risk Manager. Your goal is to analyze "
            "financial data, risk models, and internal compliance policies to "
            "provide detailed and compliant risk reports. You must use the "
            "provided tools (SQL, Document Retriever, Data Analyzer) in a logical "
            "sequence to gather data, analyze it, and formulate a final, compliant answer."
        )
        
    def __init__(self, llm: BaseLLM, tools: List[BaseTool], max_loops: int = 12):
        # Kế thừa toàn bộ logic ReAct, chỉ thay đổi persona/description
        super().__init__(llm, tools, max_loops)