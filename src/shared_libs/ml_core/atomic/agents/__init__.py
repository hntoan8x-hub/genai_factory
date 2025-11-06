"""
This module contains concrete implementations of the BaseAgent interface
for various agentic architectures like ReAct, AutoGen, and CrewAI.
"""

from .framework.react_agent import ReActAgent
from .framework.autogen_agent import AutoGenAgent
from .framework.crewai_agent import CrewAIAgent

__all__ = [
    "ReActAgent",
    "AutoGenAgent",
    "CrewAIAgent"
]
