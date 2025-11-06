# shared_libs/atomic/tools/file_storage/json_xml_parser.py
import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, Union, List
from pydantic import BaseModel, Field
from shared_libs.base.base_tool import BaseTool
from shared_libs.exceptions import ToolExecutionError

class ParserInput(BaseModel):
    """Schema for the input of the Parser Tool."""
    raw_data: str = Field(..., description="The raw JSON or XML string to parse.")
    data_type: str = Field(..., description="The type of data to parse ('json' or 'xml').")

class ParserOutput(BaseModel):
    """Schema for the output of the Parser Tool."""
    structured_data: Union[Dict, List, str] = Field(..., description="The parsed Python dictionary, list, or XML string representation.")
    success: bool = Field(..., description="Indicates if the parsing was successful.")

class JSONXMLParser(BaseTool):
    """
    A tool for safely parsing raw JSON or XML strings into structured Python objects
    that the LLM can easily consume and analyze.
    """

    @property
    def name(self) -> str:
        return "json_xml_parser"

    @property
    def description(self) -> str:
        return "Parse raw JSON or XML text into a structured dictionary/list for easier data extraction."

    @property
    def input_schema(self) -> BaseModel:
        return ParserInput
    
    @property
    def output_schema(self) -> BaseModel:
        return ParserOutput

    def _parse_json(self, raw_data: str) -> Union[Dict, List]:
        try:
            return json.loads(raw_data)
        except json.JSONDecodeError as e:
            raise ToolExecutionError(f"JSON parsing failed: {e}")

    def _parse_xml(self, raw_data: str) -> Dict:
        """Converts XML string to a basic dictionary structure."""
        try:
            root = ET.fromstring(raw_data)
            # Logic chuyển đổi XML sang Dict (tùy thuộc độ phức tạp, có thể dùng thư viện khác)
            return {root.tag: {child.tag: child.text for child in root}}
        except ET.ParseError as e:
            raise ToolExecutionError(f"XML parsing failed: {e}")

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous execution of the parsing logic."""
        try:
            parsed_input = self.input_schema.model_validate(input_data)
            data_type = parsed_input.data_type.lower()
            
            if data_type == 'json':
                result = self._parse_json(parsed_input.raw_data)
            elif data_type == 'xml':
                result = self._parse_xml(parsed_input.raw_data)
            else:
                raise ToolExecutionError(f"Unsupported data type for parsing: {data_type}. Only 'json' or 'xml' are allowed.")
                
            return ParserOutput(structured_data=result, success=True).model_dump()
        
        except ToolExecutionError as e:
            # Re-raise Tool Execution Errors with structured output
            return ParserOutput(structured_data={"error": str(e)}, success=False).model_dump()
        except Exception as e:
            raise ToolExecutionError(f"Unhandled error during parsing: {e}")

    async def async_run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous wrapper."""
        # Parsing là CPU-bound, chạy sync là đủ (hoặc có thể dùng run_in_executor nếu cần)
        return self.run(input_data)