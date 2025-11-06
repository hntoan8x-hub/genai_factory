# shared_libs/atomic/tools/file_storage/file_reader.py
import asyncio
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, HttpUrl
from shared_libs.base.base_tool import BaseTool
from shared_libs.exceptions import ToolExecutionError
import aiofiles # Giả định sử dụng aiofiles cho I/O bất đồng bộ

class FileReaderInput(BaseModel):
    """Schema for the input of the File Reader Tool."""
    file_uri: str = Field(..., description="The URI (local path, S3, or GCS URL) of the file to read.")
    max_bytes: int = Field(1048576, description="Maximum number of bytes to read (1MB limit for safety).")

class FileReaderOutput(BaseModel):
    """Schema for the output of the File Reader Tool."""
    content: str = Field(..., description="The read content of the file (truncated if over limit).")
    size_bytes: int = Field(..., description="The size of the content read.")
    success: bool = Field(..., description="Indicates if the file read was successful.")

class FileReader(BaseTool):
    """
    A hardened tool for reading the raw content of a file from a specified URI
    (S3/local), enforcing a size limit to prevent resource exhaustion (Cost/DoS Hardening).
    """

    @property
    def name(self) -> str:
        return "file_reader"

    @property
    def description(self) -> str:
        return "Reads the raw content of a file from a specified URI (local path or cloud storage URL)."

    @property
    def input_schema(self) -> BaseModel:
        return FileReaderInput
    
    @property
    def output_schema(self) -> BaseModel:
        return FileReaderOutput

    def __init__(self):
        # Trong production, cần client S3/GCS được khởi tạo
        pass 

    async def async_read_s3_gcs(self, uri: str, max_bytes: int) -> str:
        """Mô phỏng đọc file từ S3/GCS (cần thư viện async S3/GCS thực tế)."""
        if uri.startswith("s3://") or uri.startswith("gs://"):
            # Logic gọi async S3 client ở đây
            return f"Mock content retrieved from {uri}. This content has sensitive data about financial risk."[:max_bytes]
        
        # Nếu là local file, sử dụng aiofiles
        try:
            async with aiofiles.open(uri, mode='r', encoding='utf-8') as f:
                return await f.read(max_bytes)
        except Exception:
            raise ToolExecutionError(f"Local file I/O failed for {uri}.")


    async def async_run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronously runs the file reading process."""
        try:
            parsed_input = self.input_schema.model_validate(input_data)
            uri = parsed_input.file_uri
            max_bytes = parsed_input.max_bytes
            
            content = await self.async_read_s3_gcs(uri, max_bytes)

            if len(content.encode('utf-8')) >= max_bytes:
                content += "\n[CONTENT TRUNCATED BY SIZE LIMIT]"

            return FileReaderOutput(
                content=content,
                size_bytes=len(content.encode('utf-8')),
                success=True
            ).model_dump()
        
        except ToolExecutionError as e:
             raise
        except Exception as e:
            raise ToolExecutionError(f"Failed to read file: {e.__class__.__name__}: {str(e)}")

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper."""
        return asyncio.run(self.async_run(input_data))