import unittest
from unittest.mock import MagicMock, patch
from GenAI_Factory.domain_models.genai_assistant.services.assistant_service import AssistantService

class TestAssistantService(unittest.TestCase):
    @patch('GenAI_Factory.domain_models.genai_assistant.services.assistant_inference.AssistantInference')
    @patch('GenAI_Factory.domain_models.genai_assistant.services.memory_service.MemoryService')
    @patch('GenAI_Factory.domain_models.genai_assistant.services.tool_service.ToolService')
    def setUp(self, MockToolService, MockMemoryService, MockAssistantInference):
        self.mock_config = {}
        self.mock_memory_service = MockMemoryService.return_value
        self.mock_assistant_inference = MockAssistantInference.return_value
        self.mock_tool_service = MockToolService.return_value
        self.service = AssistantService(self.mock_config)

    def test_invoke_success(self):
        """Test that the invoke method correctly processes a request."""
        self.mock_assistant_inference.run_inference.return_value = {"text": "Hello, world!"}
        response = self.service.invoke({"text": "Hello"})
        self.assertEqual(response.get("text"), "Hello, world!")
        self.mock_assistant_inference.run_inference.assert_called_once()
        self.mock_memory_service.update_memory.assert_called_once()

    def test_invoke_with_invalid_input(self):
        """Test that the invoke method handles invalid input gracefully."""
        self.mock_assistant_inference.run_inference.side_effect = ValueError("Invalid input")
        with self.assertRaises(ValueError):
            self.service.invoke({"text": ""})
