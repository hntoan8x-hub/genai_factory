# shared_libs/base/base_tool.py

from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel, ValidationError

# Import the necessary exception
from shared_libs.utils.exceptions import ToolInputValidationError, ToolExecutionError 

class BaseTool(ABC):
    """
    Interface for tools that can be used by agents.
    Enforces strong data contracts, asynchronous execution, and input validation.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """A unique, human-readable name for the tool."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """A detailed description of the tool's purpose for the agent's reasoning."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> BaseModel:
        """Pydantic schema describing the required tool input."""
        pass

    @property
    @abstractmethod
    def output_schema(self) -> BaseModel:
        """Pydantic schema describing the expected tool output."""
        pass

    # --- Execution Methods ---
    
    @abstractmethod
    def _execute(self, validated_input: BaseModel) -> Any:
        """
        The internal, core execution logic of the tool. 
        It MUST accept a Pydantic model instance.
        """
        pass
    
    @abstractmethod
    async def _async_execute(self, validated_input: BaseModel) -> Any:
        """
        The internal, core asynchronous execution logic of the tool.
        """
        pass

    # --- Public Runner (HARDENING: Enforcing Validation) ---
    def run(self, input_data: Dict[str, Any]) -> Any:
        """
        Synchronously runs the tool after validating input against the schema.
        """
        validated_input = self._validate_input(input_data)
        return self._execute(validated_input)

    async def async_run(self, input_data: Dict[str, Any]) -> Any:
        """
        Asynchronously runs the tool after validating input against the schema.
        This is the preferred method for agent orchestration. (HARDENING ADDITION)
        """
        validated_input = self._validate_input(input_data)
        return await self._async_execute(validated_input)
    
    # --- Internal Validation Logic (HARDENING: Centralized Security Check) ---
    def _validate_input(self, input_data: Dict[str, Any]) -> BaseModel:
        """Validates the raw dictionary input against the Pydantic schema."""
        try:
            # Pydantic validation handles conversion and strict type checking
            return self.input_schema(**input_data)
        except ValidationError as e:
            # Raise a custom, structured exception for Agent to handle
            raise ToolInputValidationError(
                f"Input validation failed for tool {self.name}. Error: {e.errors()}"
            ) from e