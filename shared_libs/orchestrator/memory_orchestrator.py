from typing import Any, Dict, List
from shared_libs.base.base_memory import BaseMemory

class MemoryOrchestrator:
    """
    A dedicated orchestrator for managing the lifecycle of context and memory.

    This class handles the storage, retrieval, and summarization of conversation
    history or other long-term data for an agent.
    """

    def __init__(self, memory_provider: BaseMemory):
        """
        Initializes the Memory Orchestrator.

        Args:
            memory_provider (BaseMemory): The concrete memory implementation to use
                                          (e.g., Redis, ChromaDB).
        """
        self.memory_provider = memory_provider

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
