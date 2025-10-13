import unittest
from unittest.mock import MagicMock
from GenAI_Factory.domain_models.genai_assistant.pipelines.conversation_pipeline import ConversationPipeline

class TestConversationPipeline(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock()
        self.mock_llm.generate.return_value = "This is a response."
        self.mock_memory_service = MagicMock()
        self.mock_memory_service.retrieve.return_value = ["history"]
        self.pipeline = ConversationPipeline(self.mock_llm, self.mock_memory_service)

    def test_run_conversation_pipeline(self):
        """Test the basic flow of the conversation pipeline."""
        input_text = "What is the capital of France?"
        response = self.pipeline.run(input_text, "user123")
        
        self.assertEqual(response, "This is a response.")
        self.mock_memory_service.retrieve.assert_called_once_with("user123")
        self.mock_llm.generate.assert_called_once()
