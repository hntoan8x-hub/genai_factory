from typing import Any, List, Dict, Tuple
import logging
import uuid
import re # Sử dụng Regular Expressions cho việc chia tách

from shared_libs.ingestion.base.base_chunker import BaseChunker
from shared_libs.utils.exceptions import GenAIFactoryError

logger = logging.getLogger(__name__)

class RecursiveChunker(BaseChunker):
    """
    Implements a recursive text splitter that attempts to split text using a defined list 
    of separators (e.g., "\n\n", "\n", " ", etc.) in order until chunks are small enough.
    """

    def __init__(self, chunk_size: int, chunk_overlap: int, separators: List[str] = None, **kwargs):
        """
        Initializes the Recursive Chunker.
        
        Args:
            separators: A list of delimiters to use in descending order of preference.
        """
        super().__init__(chunk_size, chunk_overlap, **kwargs)
        # Các dấu phân tách mặc định
        self._separators = separators or ["\n\n", "\n", ".", " ", ""]
        logger.info(f"RecursiveChunker initialized. Strategy: {self._separators[:3]}... overlap: {chunk_overlap}")

    def _split_text_with_overlap(self, text: str) -> List[str]:
        """
        Internal logic to perform recursive splitting and manage overlapping content.
        NOTE: This is a simplified split for demonstration.
        """
        final_chunks = []
        current_text = text
        
        # MOCK LOGIC: Lặp qua các separator để chia nhỏ
        for sep in self._separators:
            if not sep: # Nếu là separator rỗng (chia theo ký tự), ta dừng lại
                break 

            parts = current_text.split(sep)
            
            new_parts = []
            for part in parts:
                while len(part) > self.chunk_size:
                    # Chia phần quá lớn
                    split_point = self.chunk_size - self.chunk_overlap
                    new_parts.append(part[:self.chunk_size])
                    part = part[split_point:] # Giữ lại phần overlap cho lần tiếp theo
                new_parts.append(part)

            if all(len(p) <= self.chunk_size for p in new_parts):
                 # Nếu tất cả các phần đã đủ nhỏ, ta dừng lại và trả về
                 current_text = new_parts
                 break
            else:
                # Nếu vẫn còn phần quá lớn, tiếp tục với separator tiếp theo
                current_text = sep.join(new_parts)

        # Đảm bảo output là list[str] và xử lý các phần tử không phải string nếu logic mock phức tạp
        if isinstance(current_text, list):
            final_chunks = [c for c in current_text if c.strip()]
        else:
            final_chunks = [current_text]

        return final_chunks

    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Splits the input text using the recursive strategy.
        """
        if not text:
            return []
            
        try:
            raw_chunks = self._split_text_with_overlap(text)
            
            chunked_data = []
            for i, chunk_content in enumerate(raw_chunks):
                # Hardening: Tạo metadata riêng cho từng đoạn
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_id": f"{metadata.get('source_id', 'N/A')}_{i}",
                    "chunk_seq_num": i,
                    "text_source": chunk_content # Lưu nội dung đoạn vào metadata (tùy chọn)
                })
                chunked_data.append((chunk_content, chunk_metadata))
                
            return chunked_data
            
        except Exception as e:
            logger.error(f"Recursive chunking failed for document {metadata.get('source_id')}: {e}")
            raise GenAIFactoryError("Chunking failed during processing.") from e