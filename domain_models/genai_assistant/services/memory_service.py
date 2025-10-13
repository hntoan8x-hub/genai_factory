from typing import Dict, Any, List
from shared_libs.genai.utils.memory_manager import MemoryManager

class MemoryService:
    """
    Service for interacting with the assistant's long-term memory.
    
    This service abstracts the underlying memory management, providing a
    clean interface for other components to store and retrieve data.
    """
    
    def __init__(self):
        """Initializes the memory manager."""
        self.memory_manager = MemoryManager()
        
    def store_conversation(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Stores a new piece of conversation data.
        
        Args:
            session_id (str): The unique ID of the conversation.
            data (Dict[str, Any]): The data to store.
        """
        self.memory_manager.store(session_id, data)
        
    def retrieve_history(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieves the conversation history for a given session.
        
        Args:
            session_id (str): The unique ID of the conversation.
            
        Returns:
            Dict[str, Any]: The retrieved history.
        """
        return self.memory_manager.retrieve(session_id)
    
    def summarize_history(self, session_id: str) -> str:
        """
        Generates a summary of the conversation history.
        
        Args:
            session_id (str): The unique ID of the conversation.
            
        Returns:
            str: The generated summary.
        """
        return self.memory_manager.summarize(session_id)
