from typing import Dict, Any, List
from shared_libs.genai.factory.llm_factory import LLMFactory
from shared_libs.genai.factory.prompt_factory import PromptFactory

class RAGPipeline:
    """
    Implements a Retrieval-Augmented Generation (RAG) pipeline.

    This pipeline retrieves relevant documents from a knowledge base and uses them
    as context for generating a grounded response.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the RAGPipeline with configuration.

        Args:
            config (Dict[str, Any]): The configuration dictionary for this pipeline.
        """
        self.config = config
        self.llm = LLMFactory.build(config.get("llm", {}))
        self.rag_prompt = PromptFactory.build(config.get("rag_prompt", {}))
        
        # Placeholder for a retriever component
        self.retriever = self._setup_retriever(config.get("retrieval", {}))

    def _setup_retriever(self, retrieval_config: Dict[str, Any]) -> Any:
        """
        Sets up the retriever based on configuration.

        This is a simplified placeholder. In a real application, this would
        instantiate a vector database client (e.g., ChromaDB, Weaviate).

        Args:
            retrieval_config (Dict[str, Any]): The retrieval-specific configuration.

        Returns:
            Any: A mock retriever object.
        """
        print("Setting up mock retriever...")
        # Simulating a knowledge base as a simple dictionary
        return {
            "GenAI is a field of artificial intelligence that focuses on creating new, original content.": "genai_doc_1",
            "Retrieval-Augmented Generation (RAG) improves LLM accuracy by grounding it in external data.": "rag_doc_1",
            "The LLM Factory builds various LLM instances from a configuration.": "llm_doc_1",
            "The GenAI Assistant is designed for production use.": "assistant_doc_1",
        }

    def run(self, query: str) -> Dict[str, Any]:
        """
        Executes the RAG pipeline.

        Args:
            query (str): The user's input query.

        Returns:
            Dict[str, Any]: A dictionary containing the grounded response and sources.
        """
        print("Executing RAG pipeline...")
        
        # 1. Retrieve relevant context (simplified)
        retrieved_text = ""
        for doc_text, doc_id in self.retriever.items():
            if any(keyword in query.lower() for keyword in ["genai", "llm", "rag", "assistant"]):
                retrieved_text = doc_text
                break
        
        if not retrieved_text:
            return {"response": "I couldn't find any relevant information on that topic.", "sources": []}

        # 2. Render the prompt with the retrieved context
        rendered_prompt = self.rag_prompt.render(context={"context": retrieved_text, "question": query})
        
        # 3. Generate a response from the LLM
        print("Generating grounded response...")
        try:
            response = self.llm.generate(prompt=rendered_prompt)
        except Exception as e:
            return {"error": str(e)}

        print("RAG pipeline completed.")
        return {
            "response": response,
            "sources": [retrieved_text],
        }
