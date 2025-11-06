# shared_libs/atomic/agents/autogen_agent.py

from typing import Any, Dict, List, Optional, Union
from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_llm import BaseLLM
import asyncio

class AutoGenAgent(BaseAgent):
    """
    A single agent class representing a participant in an AutoGen-style conversation.
    This agent adheres to the asynchronous BaseAgent contract, enabling its use
    within a non-blocking multi-agent orchestrator.
    """

    def __init__(self, llm: BaseLLM, role: str, name: str, description: str):
        """
        Initializes the agent with a language model and a defined role.

        Args:
            llm (BaseLLM): The language model for this agent.
            role (str): The specific role or persona of the agent (e.g., "Data Analyst").
            name (str): The name of the agent.
            description (str): A detailed description of the agent's capabilities.
        """
        # Note: Calling super().__init__() is good practice if BaseAgent had a constructor.
        self.llm = llm
        self._role = role
        self._name = name
        self._description = description
        self.context: Dict[str, Any] = {}
        self.history: List[Dict[str, str]] = [] # Tracking internal history for chat

    # --- BaseAgent Properties (HARDENING: Contract Completion) ---
    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    # --- Core Reasoning Methods ---

    def plan(self, query: str, context: Dict[str, Any] = {}) -> str:
        """Synchronous implementation of the planning step."""
        system_message = (
            f"You are {self.name}, a {self._role}. {self.description}. "
            f"Based on the following query, provide a detailed plan to solve it."
        )
        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": query}]
        return self.llm.chat(messages)

    async def async_plan(self, query: str, context: Dict[str, Any] = {}) -> str:
        """Asynchronous planning step. (HARDENING: Uses LLM's async_chat)"""
        system_message = (
            f"You are {self.name}, a {self._role}. {self.description}. "
            f"Based on the following query, provide a detailed plan to solve it."
        )
        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": query}]
        return await self.llm.async_chat(messages)

    def act(self, input_message: str, **kwargs) -> str:
        """Synchronous execution of the action (generating response in this context)."""
        system_message = (f"You are {self.name}, a {self._role}. {self.description}. Analyze the conversation history and provide your next response.")
        
        # Add the incoming message to the current chat history for context
        current_messages = self.history + [{"role": "user", "content": input_message}]
        
        response = self.llm.chat(current_messages)
        self.history.append({"role": "user", "content": input_message})
        self.history.append({"role": "assistant", "content": response})
        return response

    async def async_act(self, input_message: str, **kwargs) -> str:
        """Asynchronous execution of the action. (HARDENING: Uses LLM's async_chat)"""
        system_message = (f"You are {self.name}, a {self._role}. {self.description}. Analyze the conversation history and provide your next response.")
        
        current_messages = self.history + [{"role": "user", "content": input_message}]
        
        response = await self.llm.async_chat(current_messages)
        self.history.append({"role": "user", "content": input_message})
        self.history.append({"role": "assistant", "content": response})
        return response

    def observe(self, observation: Any) -> None:
        """Updates the agent's internal state or context based on an observation."""
        # For AutoGen style, observation is often just a new message/history update
        if isinstance(observation, dict) and 'role' in observation and 'content' in observation:
            self.history.append(observation)
        # Fallback to general context update
        if "context_history" in self.context:
            self.context["context_history"].append(observation)
        else:
            self.context["context_history"] = [observation]

    # --- Loop Implementations (HARDENING: Contract Fulfillment) ---
    # These methods must raise NotImplementedError as the loop is external.

    def loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        """
        Placeholder for a single-agent loop. 
        Raises an error to enforce orchestration by the central manager.
        """
        raise NotImplementedError("AutoGen agents operate within an external multi-agent orchestrator.")

    async def async_loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        """
        Placeholder for the asynchronous single-agent loop.
        Raises an error to enforce orchestration by the central manager.
        """
        raise NotImplementedError("AutoGen agents operate within an external multi-agent orchestrator.")