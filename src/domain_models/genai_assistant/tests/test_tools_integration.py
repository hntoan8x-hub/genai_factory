import unittest
from unittest.mock import MagicMock, patch
from shared_libs.genai.atomic.tools.sql_tool import SQLTool
from shared_libs.genai.atomic.tools.web_tool import WebTool

class TestTools(unittest.TestCase):

    @patch('GenAI_Factory.domain_models.genai_assistant.services.tool_service.requests.get')
    def test_web_tool_run(self, mock_get):
        """Test that the WebTool can successfully perform a web search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "This is a sample webpage content."
        mock_get.return_value = mock_response

        tool = WebTool()
        result = tool.run({"query": "test query"})
        
        self.assertEqual(result.get("status"), "success")
        self.assertIn("sample webpage content", result.get("output"))

    @patch('shared_libs.genai.atomic.tools.sql_tool.pymysql.connect')
    def test_sql_tool_run(self, mock_connect):
        """Test that the SQLTool can successfully execute a query."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("John",), ("Jane",)]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        tool = SQLTool()
        result = tool.run({"query": "SELECT name FROM users"})

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("output"), "[('John',), ('Jane',)]")
        mock_connect.assert_called_once()
        mock_cursor.execute.assert_called_once_with("SELECT name FROM users")
