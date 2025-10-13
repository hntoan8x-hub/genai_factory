"""
This module contains concrete implementations of the BaseAgent interface
for various agentic architectures like ReAct, AutoGen, and CrewAI.
"""

from .react_agent import ReActAgent
from .autogen_agent import AutoGenAgent
from .crewai_agent import CrewAIAgent

__all__ = [
    "ReActAgent",
    "AutoGenAgent",
    "CrewAIAgent"
]
