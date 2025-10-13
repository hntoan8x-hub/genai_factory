# shared_libs/base/base_memory.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseMemory(ABC):
    """
    Interface for memory systems.
    Memory manages context and history for sessions.
    Enforces asynchronous I/O for high performance and non-blocking operations. (HARDENING)
    """

    # --- Synchronous Methods (Current State) ---
    @abstractmethod
    def store(self, key: str, value: Any) -> None:
        """Stores a value into memory."""
        pass

    @abstractmethod
    def retrieve(self, key: str) -> Any:
        """Retrieves a value from memory based on the key."""
        pass

    @abstractmethod
    def summarize(self, keys: List[str]) -> str:
        """Summarizes the content associated with a list of keys."""
        pass

    # --- Asynchronous Methods (HARDENING ADDITIONS) ---
    @abstractmethod
    async def async_store(self, key: str, value: Any) -> None:
        """Asynchronously stores a value into memory. (Preferred for production)"""
        pass

    @abstractmethod
    async def async_retrieve(self, key: str) -> Any:
        """Asynchronously retrieves a value from memory based on the key. (Preferred for production)"""
        pass

    @abstractmethod
    async def async_summarize(self, keys: List[str]) -> str:
        """Asynchronously summarizes the content associated with a list of keys."""
        pass