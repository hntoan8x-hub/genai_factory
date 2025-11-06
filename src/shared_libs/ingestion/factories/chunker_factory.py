from typing import Dict, Any, Type
import logging
from shared_libs.ingestion.base.base_chunker import BaseChunker
from shared_libs.ingestion.chunkers.recursive_chunker import RecursiveChunker
from shared_libs.ingestion.chunkers.markdown_chunker import MarkdownChunker
from shared_libs.ingestion.configs.rag_ingestion_config_schema import ChunkingConfig # Import Schema
from shared_libs.utils.exceptions import GenAIFactoryError

logger = logging.getLogger(__name__)

class ChunkerFactory:
    """
    A production-grade factory for creating BaseChunker instances.
    
    It handles the instantiation and configuration injection (chunk_size, overlap) 
    based on the configured strategy.
    """
    
    # Hardening 1: Registry mapping strategy names to their concrete Chunker classes
    _registry: Dict[str, Type[BaseChunker]] = {
        "recursive_text": RecursiveChunker,
        "markdown": MarkdownChunker,
        # Thêm các Chunker khác tại đây (ví dụ: "html": HtmlChunker)
    }

    @classmethod
    def create_chunker(cls, config: ChunkingConfig) -> BaseChunker:
        """
        Hardening 2: Creates a BaseChunker instance, injecting size and overlap parameters.
        
        Args:
            config: An instance of the validated ChunkingConfig Pydantic model.
            
        Returns:
            An instance of a class inheriting from BaseChunker.
        """
        strategy = config.strategy
        params = config.model_dump() # Dùng model_dump() để lấy tất cả params đã validated
        
        if strategy not in cls._registry:
            logger.error(f"ChunkerFactory error: Unsupported chunking strategy '{strategy}'.")
            raise ValueError(f"Unsupported chunking strategy: '{strategy}'")
            
        chunker_class = cls._registry[strategy]
        
        try:
            logger.info(f"Creating chunker instance: {strategy} (Size: {config.chunk_size}, Overlap: {config.chunk_overlap}).")
            
            # Instantiation: DI các tham số cốt lõi (size, overlap)
            return chunker_class(
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                # **params # Có thể truyền tất cả params nếu cần
            )
        except TypeError as e:
            error_msg = f"Failed to create chunker '{strategy}': Missing/invalid parameters in config."
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(f"{error_msg}. Details: {e}") from e
        except Exception as e:
            error_msg = f"Failed to create chunker '{strategy}'. Critical error during instantiation."
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(f"{error_msg}. Critical error: {e}") from e