# shared_libs/base/base_agent.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseAgent(ABC):
    """
    Interface for GenAI agents.
    Agents perform reasoning steps and actions.
    Enforces asynchronous execution and resource limits. (HARDENING)
    """

    # --- Properties (HARDENING ADDITION) ---
    @property
    @abstractmethod
    def name(self) -> str:
        """A unique, human-readable name for the agent."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A detailed description of the agent's core function."""
        pass

    # --- Core Reasoning Methods ---
    @abstractmethod
    def plan(self, user_input: str, context: Dict[str, Any]) -> str:
        """
        Plans the course of action based on user input and context.
        """
        pass

    @abstractmethod
    def act(self, action: str, **kwargs) -> Any:
        """
        Executes a specific action (synchronous).
        """
        pass

    @abstractmethod
    def observe(self, observation: Any) -> None:
        """
        Observes the result of an action and updates the state.
        """
        pass

    # --- Synchronous Loop ---
    @abstractmethod
    def loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        """
        Runs the main agent loop (plan, act, observe) synchronously.
        Args:
            user_input: The initial user request.
            max_steps: Maximum number of steps in the loop (Cost Control).
            timeout: Maximum time (seconds) before the loop is terminated (HARDENING ADDITION - Resource Control).

        Returns:
            The final result.
        """
        pass

    # --- Asynchronous Loop (HARDENING ADDITION - Scalability) ---
    @abstractmethod
    async def async_loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        """
        Runs the main agent loop asynchronously. 
        This is the preferred method for production environment integration (FastAPI).

        Args:
            user_input: The initial user request.
            max_steps: Maximum number of steps in the loop (Cost Control).
            timeout: Maximum time (seconds) before the loop is terminated (Resource Control).
            
        Returns:
            The final result.
        """
        pass