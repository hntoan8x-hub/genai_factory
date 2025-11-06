# shared_libs/atomic/agents/crewai_agent.py

from typing import Any, Dict, List, Optional, Union
from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_llm import BaseLLM
import asyncio

class CrewAIAgent(BaseAgent):
    """
    A single agent class for a CrewAI-style multi-agent system.
    Adheres to the async BaseAgent contract for non-blocking orchestration.
    """

    def __init__(self, llm: BaseLLM, role: str, goal: str, backstory: str, name: str, description: str, tools: Optional[List[Any]] = None):
        """
        Initializes the agent with its persona and tools.
        """
        super().__init__()
        self.llm = llm
        self._role = role
        self._goal = goal
        self._backstory = backstory
        self.tools = tools if tools is not None else []
        self._name = name
        self._description = description
        self.context: Dict[str, Any] = {}
        self.history: List[Dict[str, str]] = []

    # --- BaseAgent Properties (HARDENING: Contract Completion) ---
    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    # --- Core Reasoning Methods (Synchronous) ---
    def plan(self, query: str, context: Dict[str, Any] = {}) -> str:
        """Generates a synchronous plan based on the query."""
        system_message = (
            f"You are a skilled {self._role} with the goal of '{self._goal}'. "
            f"Your backstory is: '{self._backstory}'. "
            f"Based on the task '{query}', outline a detailed plan to achieve your goal. "
            f"You have access to the following tools: {[tool.__class__.__name__ for tool in self.tools]}."
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": query}
        ]
        return self.llm.chat(messages)

    def act(self, input_message: str, **kwargs) -> str:
        """Synchronously executes an action (generating a response or tool call decision)."""
        system_message = (f"You are a {self._role} and your goal is '{self._goal}'. Based on the following input, provide your next response or use a tool. Input: {input_message}")
        
        # Add the incoming message to the current chat history for context
        current_messages = self.history + [{"role": "user", "content": input_message}]
        
        response = self.llm.chat(current_messages)
        self.history.append({"role": "user", "content": input_message})
        self.history.append({"role": "assistant", "content": response})
        return response

    # --- Core Reasoning Methods (Asynchronous - HARDENING) ---
    async def async_plan(self, query: str, context: Dict[str, Any] = {}) -> str:
        """Asynchronously generates a plan. (Uses LLM's async_chat)"""
        system_message = (
            f"You are a skilled {self._role} with the goal of '{self._goal}'. "
            f"Your backstory is: '{self._backstory}'. "
            f"Based on the task '{query}', outline a detailed plan to achieve your goal. "
            f"You have access to the following tools: {[tool.__class__.__name__ for tool in self.tools]}."
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": query}
        ]
        return await self.llm.async_chat(messages)

    async def async_act(self, input_message: str, **kwargs) -> str:
        """Asynchronously executes an action. (Uses LLM's async_chat)"""
        system_message = (f"You are a {self._role} and your goal is '{self._goal}'. Based on the following input, provide your next response or use a tool. Input: {input_message}")
        
        current_messages = self.history + [{"role": "user", "content": input_message}]
        
        response = await self.llm.async_chat(current_messages)
        self.history.append({"role": "user", "content": input_message})
        self.history.append({"role": "assistant", "content": response})
        return response

    def observe(self, observation: Any) -> None:
        """Updates the agent's state or context based on a new observation."""
        self.context["observation"] = observation

    # --- Loop Implementations (HARDENING: Contract Fulfillment) ---
    def loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        """
        Placeholder for the synchronous single-agent loop. 
        Enforces orchestration by the external crew manager.
        """
        raise NotImplementedError("CrewAI agents must be managed by an external crew/orchestrator.")

    async def async_loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        """
        Placeholder for the asynchronous single-agent loop.
        Enforces orchestration by the external crew manager.
        """
        raise NotImplementedError("CrewAI agents must be managed by an external crew/orchestrator.")
