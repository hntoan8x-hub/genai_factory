from typing import Dict, Any, List
from shared_libs.genai.factory.llm_factory import LLMFactory
from shared_libs.genai.utils.memory_manager import MemoryManager

class ConversationPipeline:
    """
    Manages a multi-turn conversation, incorporating memory for context.

    This pipeline retrieves conversation history, generates a new response, and
    stores the updated history for the next turn.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the ConversationPipeline with configuration.

        Args:
            config (Dict[str, Any]): The configuration dictionary for this pipeline.
        """
        self.config = config
        self.llm = LLMFactory.build(config.get("llm", {}))
        self.memory = MemoryManager()

    def run(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Executes the conversation pipeline.

        Args:
            user_id (str): A unique identifier for the user to retrieve their history.
            query (str): The user's input query.

        Returns:
            Dict[str, Any]: A dictionary containing the response and updated history.
        """
        print(f"[{user_id}] Executing conversation pipeline...")

        # 1. Retrieve conversation history
        history = self.memory.retrieve(user_id)
        
        # 2. Add current query to history (simplified for demonstration)
        current_history = history.get("history", [])
        current_history.append({"role": "user", "content": query})
        
        # 3. Generate a response from the LLM based on the full conversation history
        print(f"[{user_id}] Generating response from LLM...")
        try:
            # Note: A real implementation would pass the full `current_history` to the LLM
            response = self.llm.generate(prompt=query)
        except Exception as e:
            return {"error": str(e)}

        # 4. Add the LLM's response to history
        current_history.append({"role": "assistant", "content": response})

        # 5. Store the updated history
        self.memory.store(user_id, {"history": current_history})
        
        print(f"[{user_id}] Conversation pipeline completed.")
        return {
            "response": response,
            "session_id": user_id,
        }
