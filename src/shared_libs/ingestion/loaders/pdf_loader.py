from typing import Any, Dict
import logging
import asyncio
import os
# Giả định thư viện xử lý PDF (ví dụ: PyPDF2)
try:
    import pypdf
except ImportError:
    pypdf = None

from shared_libs.ingestion.base.base_loader import BaseLoader
from shared_libs.utils.exceptions import GenAIFactoryError

logger = logging.getLogger(__name__)

class PDFLoader(BaseLoader):
    """
    A concrete loader for PDF files. Implements asynchronous loading by offloading 
    the synchronous PDF reading operation to a thread.
    """
    
    @property
    def supported_file_type(self) -> str:
        return "pdf"

    def _extract_text_sync(self, file_path: str) -> Dict[str, Any]:
        """
        Internal synchronous method to read the PDF file and extract text/metadata.
        (THIS IS THE BLOCKING OPERATION)
        """
        if pypdf is None:
            raise ImportError("The 'pypdf' library is required for PDFLoader.")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at path: {file_path}")

        raw_text = ""
        total_pages = 0
        try:
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                total_pages = len(reader.pages)
                
                for page in reader.pages:
                    raw_text += page.extract_text() or ""
            
            return {
                'content': raw_text,
                'metadata': {
                    'source_path': file_path,
                    'file_type': self.supported_file_type,
                    'total_pages': total_pages
                }
            }
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {file_path}: {e}")
            raise GenAIFactoryError(f"PDF extraction failed for {file_path}.")

    async def async_load(self, file_path_or_data: Any) -> Dict[str, Any]:
        """
        Hardening: Asynchronously loads the PDF by running the synchronous logic 
        in a separate thread using asyncio.to_thread.
        """
        if not isinstance(file_path_or_data, str):
            raise TypeError("PDFLoader expects a file path string for loading.")
            
        logger.info(f"Starting async extraction for PDF: {file_path_or_data}")
        
        # Offload blocking _extract_text_sync to a thread
        return await asyncio.to_thread(self._extract_text_sync, file_path_or_data)