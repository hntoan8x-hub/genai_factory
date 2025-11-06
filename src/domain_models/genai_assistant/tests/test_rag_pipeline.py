import unittest
from unittest.mock import MagicMock
from GenAI_Factory.domain_models.genai_assistant.pipelines.rag_pipeline import RAGPipeline

class TestRAGPipeline(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock()
        self.mock_llm.generate.return_value = "This is a grounded response."
        self.mock_retriever = MagicMock()
        self.mock_retriever.retrieve.return_value = ["doc1", "doc2"]
        self.mock_reranker = MagicMock()
        self.mock_reranker.rerank.return_value = ["doc2", "doc1"]
        self.pipeline = RAGPipeline(self.mock_llm, self.mock_retriever, self.mock_reranker)

    def test_run_rag_pipeline(self):
        """Test the end-to-end flow of the RAG pipeline."""
        input_text = "Who is the CEO of Google?"
        response = self.pipeline.run(input_text)
        
        self.assertEqual(response, "This is a grounded response.")
        self.mock_retriever.retrieve.assert_called_once_with(input_text)
        self.mock_reranker.rerank.assert_called_once()
        self.mock_llm.generate.assert_called_once()
