import unittest
from unittest.mock import patch, mock_open
import json
from GenAI_Factory.domain_models.genai_assistant.logging.interaction_logger import log_interaction
from GenAI_Factory.domain_models.genai_assistant.logging.audit_logger import log_audit_event
from GenAI_Factory.domain_models.genai_assistant.logging.mlflow_adapter import MLflowAdapter

class TestLogging(unittest.TestCase):

    @patch("GenAI_Factory.domain_models.genai_assistant.logging.interaction_logger.logging.FileHandler")
    @patch("GenAI_Factory.domain_models.genai_assistant.logging.interaction_logger.logging.getLogger")
    def test_interaction_logger(self, mock_get_logger, mock_file_handler):
        """Test that interaction logs are correctly formatted and logged."""
        mock_logger = mock_get_logger.return_value
        log_interaction("user123", {"query": "Hello"}, {"text": "Hi"})
        
        mock_logger.info.assert_called_once()
        logged_message = mock_logger.info.call_args[0][0]
        log_data = json.loads(logged_message)
        
        self.assertEqual(log_data["user_id"], "user123")
        self.assertEqual(log_data["input"]["query"], "Hello")
        self.assertEqual(log_data["output"]["text"], "Hi")

    @patch("GenAI_Factory.domain_models.genai_assistant.logging.audit_logger.logging.FileHandler")
    @patch("GenAI_Factory.domain_models.genai_assistant.logging.audit_logger.logging.getLogger")
    def test_audit_logger(self, mock_get_logger, mock_file_handler):
        """Test that audit logs are correctly formatted and logged."""
        mock_logger = mock_get_logger.return_value
        log_audit_event("prompt_denied", "user456", {"reason": "safety"})
        
        mock_logger.info.assert_called_once()
        logged_message = mock_logger.info.call_args[0][0]
        log_data = json.loads(logged_message)
        
        self.assertEqual(log_data["event_type"], "prompt_denied")
        self.assertEqual(log_data["user_id"], "user456")
        self.assertEqual(log_data["details"]["reason"], "safety")

    @patch("GenAI_Factory.domain_models.genai_assistant.logging.mlflow.set_experiment")
    @patch("GenAI_Factory.domain_models.genai_assistant.logging.mlflow.start_run")
    def test_mlflow_adapter(self, mock_start_run, mock_set_experiment):
        """Test that the MLflow adapter logs parameters and metrics correctly."""
        adapter = MLflowAdapter("test_experiment")
        mock_start_run.return_value.__enter__.return_value = None
        
        adapter.log_run("test_run", {"param1": 1}, {"metric1": 0.9})
        
        mock_set_experiment.assert_called_once_with("test_experiment")
        mock_start_run.assert_called_once_with(run_name="test_run")
