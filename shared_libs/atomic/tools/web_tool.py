from typing import Any, Dict, List
from pydantic import BaseModel, Field
from shared_libs.genai.base.base_tool import BaseTool

class WebSearchInput(BaseModel):
    """Schema for the input of the Web Search Tool."""
    query: str = Field(..., description="The search query string.")
    max_results: int = Field(5, description="The maximum number of search results to return.")

class WebSearchOutput(BaseModel):
    """Schema for the output of the Web Search Tool."""
    results: List[Dict[str, str]] = Field(..., description="A list of search results.")

class WebTool(BaseTool):
    """
    A tool for performing web searches.

    This tool simulates searching the web for information, providing a way for the
    agent to access up-to-date or external data.
    """

    @property
    def input_schema(self) -> BaseModel:
        return WebSearchInput

    @property
    def output_schema(self) -> BaseModel:
        return WebSearchOutput

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs a web search based on the input query.

        Note: This is a placeholder implementation. In a production environment,
        this would integrate with a real search API (e.g., Google Search API).

        Args:
            input_data (Dict[str, Any]): The input data containing the 'query' and 'max_results'.

        Returns:
            Dict[str, Any]: A dictionary containing the search results.
        """
        try:
            parsed_input = self.input_schema.model_validate(input_data)
            query = parsed_input.query
            max_results = parsed_input.max_results
            
            print(f"Searching the web for: {query}")
            
            # Simulate a few search results
            mock_results = [
                {"title": f"Result 1 for {query}", "url": "https://example.com/result1", "snippet": "A brief description of the first search result."},
                {"title": f"Result 2 for {query}", "url": "https://example.com/result2", "snippet": "A brief description of the second search result."},
                {"title": f"Result 3 for {query}", "url": "https://example.com/result3", "snippet": "A brief description of the third search result."}
            ]
            
            return {"results": mock_results[:max_results]}
        
        except Exception as e:
            return {"results": [], "error": str(e)}
