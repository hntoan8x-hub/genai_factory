from typing import Any, List, Dict, Tuple
import logging
import re

from shared_libs.ingestion.base.base_chunker import BaseChunker
from shared_libs.utils.exceptions import GenAIFactoryError

logger = logging.getLogger(__name__)

# Hardening 1: Định nghĩa các dấu phân tách Markdown ưu tiên
MARKDOWN_SEPARATORS = [
    r"\n#{1,6} ",  # Tiêu đề Markdown (#, ##, ...)
    r"\n\*\*\*+\n", # Dấu gạch ngang phân cách
    r"\n---+\n",    # Dấu gạch ngang phân cách
    r"\n\n",        # Đoạn mới
    r"\n",          # Dòng mới
    " ",            # Từ
    "",             # Ký tự
]

class MarkdownChunker(BaseChunker):
    """
    Implements a structural text splitter specifically optimized for Markdown documents.
    It splits based on Markdown headers to keep semantically related content together.
    """
    
    def __init__(self, chunk_size: int, chunk_overlap: int, **kwargs):
        super().__init__(chunk_size, chunk_overlap, **kwargs)
        logger.info("MarkdownChunker initialized. Strategy: Structural split based on headers.")

    def _split_markdown_structurally(self, text: str) -> List[str]:
        """
        Internal logic to split text primarily by Markdown headers, then fall back
        to recursive splitting if chunks are still too large.
        """
        current_text = text
        final_chunks = []
        
        # 1. Chia theo các dấu phân tách cấu trúc (headers, đoạn)
        for sep in MARKDOWN_SEPARATORS:
            if re.match(r"\n", sep):
                parts = re.split(sep, current_text)
            else:
                parts = current_text.split(sep)
            
            # 2. Xử lý các phần (parts)
            new_parts = []
            for part in parts:
                # Nếu phần đã nhỏ, giữ lại
                if len(part) <= self.chunk_size:
                    new_parts.append(part)
                else:
                    # Nếu phần còn quá lớn, sử dụng logic recursive (giả lập)
                    # NOTE: Trong thực tế, đây là nơi ta gọi RecursiveChunker.chunk()
                    new_parts.extend(self._recursive_fallback(part))
            
            current_text = '\n\n'.join(new_parts) # Dùng separator tiếp theo trên kết quả
            
            # MOCK DỪNG
            if all(len(p) <= self.chunk_size for p in new_parts):
                 final_chunks = [c for c in new_parts if c.strip()]
                 return final_chunks

        # Nếu không có dấu phân tách nào hiệu quả, trả về các phần đã chia
        return [current_text]
    
    def _recursive_fallback(self, large_text: str) -> List[str]:
        """Fallback logic to handle oversized sections."""
        temp_chunks = []
        text_to_process = large_text
        while len(text_to_process) > self.chunk_size:
            split_point = self.chunk_size - self.chunk_overlap
            temp_chunks.append(text_to_process[:self.chunk_size])
            text_to_process = text_to_process[split_point:]
        temp_chunks.append(text_to_process)
        return temp_chunks
        

    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Splits the input text using the Markdown structural strategy.
        """
        if not text:
            return []
            
        try:
            raw_chunks = self._split_markdown_structurally(text)
            
            chunked_data = []
            for i, chunk_content in enumerate(raw_chunks):
                # Hardening: Tạo metadata riêng cho từng đoạn
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_id": f"{metadata.get('source_id', 'N/A')}_{i}",
                    "chunk_seq_num": i,
                    "text_source": chunk_content 
                })
                chunked_data.append((chunk_content, chunk_metadata))
                
            return chunked_data
            
        except Exception as e:
            logger.error(f"Markdown chunking failed for document {metadata.get('source_id')}: {e}")
            raise GenAIFactoryError("Chunking failed during processing.") from e