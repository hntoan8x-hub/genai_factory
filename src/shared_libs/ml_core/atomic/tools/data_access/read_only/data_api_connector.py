# shared_libs/atomic/tools/data_access/read_only/data_api_connector.py

import asyncio
import requests
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from shared_libs.base.base_tool import BaseTool
from shared_libs.exceptions import ToolExecutionError, SecurityError
from concurrent.futures import ThreadPoolExecutor

class APIConnectorInput(BaseModel):
    """Schema for the input of the Data API Connector Tool."""
    endpoint_url: str = Field(..., description="The full URL of the API endpoint to query (e.g., 'https://api.external.com/data').")
    params: Optional[Dict[str, Any]] = Field(None, description="Optional: Dictionary of query parameters for the GET request.")
    timeout: int = Field(10, description="Request timeout in seconds.")

class APIConnectorOutput(BaseModel):
    """Schema for the output of the Data API Connector Tool."""
    status_code: int = Field(..., description="The HTTP status code of the response.")
    data: Dict[str, Any] = Field(..., description="The JSON data returned from the API.")
    success: bool = Field(..., description="Indicates if the API call was successful (status code 2xx).")

class DataAPIConnector(BaseTool):
    """
    A hardened tool for executing read-only GET requests against external or internal
    API endpoints, ensuring input validation and handling non-blocking I/O.
    """

    @property
    def name(self) -> str:
        return "data_api_connector"

    @property
    def description(self) -> str:
        return "Execute read-only GET requests to external data APIs using specified query parameters."

    @property
    def input_schema(self) -> BaseModel:
        return APIConnectorInput
    
    @property
    def output_schema(self) -> BaseModel:
        return APIConnectorOutput

    def __init__(self, config: Dict[str, Any] = None):
        # Sử dụng ThreadPoolExecutor để xử lý requests.get() đồng bộ một cách an toàn
        self.executor = ThreadPoolExecutor(max_workers=5)
        # Có thể thêm logic whitelist/blacklist URL ở đây cho mục đích Hardening

    def _execute_sync(self, validated_input: APIConnectorInput) -> Dict[str, Any]:
        """Synchronous execution of the API call."""
        try:
            response = requests.get(
                validated_input.endpoint_url,
                params=validated_input.params,
                timeout=validated_input.timeout
            )
            response.raise_for_status() # Raise HTTPException for bad status codes (4xx or 5xx)
            
            data = response.json() if response.content else {}
            
            return APIConnectorOutput(
                status_code=response.status_code,
                data=data,
                success=True
            ).model_dump()

        except requests.exceptions.RequestException as e:
            status_code = e.response.status_code if e.response is not None else 500
            error_data = {"error": f"API request failed: {e.__class__.__name__}: {str(e)}"}
            
            # Vẫn trả về cấu trúc output, nhưng đánh dấu success=False
            return APIConnectorOutput(
                status_code=status_code,
                data=error_data,
                success=False
            ).model_dump()
        except Exception as e:
            raise ToolExecutionError(f"Critical error during API execution: {e}")

    async def async_run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronously runs the tool by offloading blocking I/O."""
        validated_input = self.input_schema.model_validate(input_data)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._execute_sync, validated_input)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper (discouraged in the main API flow)."""
        return asyncio.run(self.async_run(input_data))