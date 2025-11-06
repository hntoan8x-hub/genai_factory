# shared_libs/orchestrator/memory_orchestrator.py (HARDENED VERSION)

from typing import Any, Dict, List
import asyncio
from shared_libs.base.base_memory import BaseMemory
from shared_libs.utils.exceptions import GenAIFactoryError

class MemoryOrchestrator:
    """
    A dedicated asynchronous orchestrator for managing the lifecycle of context and memory.
    Handles storage, retrieval, and summarization using an asynchronous memory provider.
    """

    def __init__(self, memory_provider: BaseMemory):
        self.memory_provider = memory_provider

    async def async_store_context(self, session_id: str, data: Dict[str, Any]):
        """
        Stores data for a given session asynchronously. (HARDENING)
        """
        try:
            await self.memory_provider.async_store(session_id, data)
        except Exception as e:
            raise GenAIFactoryError(f"Failed to store context for session {session_id}: {e}")

    async def async_retrieve_context(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieves all stored context for a given session asynchronously. (HARDENING)
        """
        try:
            return await self.memory_provider.async_retrieve(session_id)
        except Exception as e:
            raise GenAIFactoryError(f"Failed to retrieve context for session {session_id}: {e}")

    async def async_summarize_context(self, session_id: str) -> str:
        """
        Summarizes the conversation history for a given session asynchronously. (HARDENING)
        """
        try:
            # Giả định memory provider xử lý logic tóm tắt bên trong
            return await self.memory_provider.async_summarize(session_id)
        except Exception as e:
            raise GenAIFactoryError(f"Failed to summarize context for session {session_id}: {e}")

    def store_context(self, session_id: str, data: Dict[str, Any]):
        """
        Stores data for a given session.

        Args:
            session_id (str): The unique identifier for the session.
            data (Dict[str, Any]): The data to be stored.
        """
        print(f"Storing context for session: {session_id}")
        self.memory_provider.store(session_id, data)

    def retrieve_context(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieves all stored context for a given session.

        Args:
            session_id (str): The unique identifier for the session.

        Returns:
            Dict[str, Any]: The retrieved context data.
        """
        print(f"Retrieving context for session: {session_id}")
        return self.memory_provider.retrieve(session_id)

    def summarize_context(self, session_id: str) -> str:
        """
        Summarizes the conversation history for a given session.

        Args:
            session_id (str): The unique identifier for the session.

        Returns:
            str: A summary of the conversation.
        """
        print(f"Summarizing context for session: {session_id}")
        return self.memory_provider.summarize(session_id)
