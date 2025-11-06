# src/shared_libs/ingestion/services/rag_ingestion_service.py

import logging
import asyncio
from typing import Dict, Any, List, Tuple
import numpy as np
import os
import itertools # Sử dụng để làm phẳng danh sách chunks

# Import các thành phần Dependency
from shared_libs.base.base_llm import BaseLLM
from shared_libs.ingestion.configs.rag_ingestion_config_schema import RAGIngestionConfig 
from shared_libs.ingestion.factories.loader_factory import LoaderFactory
from shared_libs.ingestion.factories.chunker_factory import ChunkerFactory
from shared_libs.ingestion.base.base_loader import BaseLoader
from shared_libs.ingestion.base.base_chunker import BaseChunker
from shared_libs.utils.exceptions import GenAIFactoryError

logger = logging.getLogger(__name__)

class RAGIngestionService:
    """
    The internal orchestrator for the RAG Indexing Preprocessing Layer.
    
    Manages the Load -> Chunk -> Embed pipeline, ensuring component creation via Factories 
    and efficient asynchronous execution.
    """
    
    def __init__(self, config: RAGIngestionConfig, embedding_llm: BaseLLM):
        """
        Initializes the service, building Loader(s) and the Chunker based on the validated config.
        
        Args:
            config: The validated RAGIngestionConfig (Quality Gate).
            embedding_llm: BaseLLM instance used for vector creation (Dependency Injection).
        """
        self.config = config
        self.embedding_llm = embedding_llm
        
        # Build components via Factories
        self._build_components()
        
        logger.info(f"RAGIngestionService initialized. Chunking Strategy: {self._chunker.chunk_size}/{self._chunker.chunk_overlap}")

    def _build_components(self):
        """Hardening 1: Builds all necessary Loaders and the single Chunker instance."""
        try:
            # 1. Build Chunker (Sử dụng config đã validated)
            self._chunker: BaseChunker = ChunkerFactory.create_chunker(self.config.chunking)
            
            # 2. Build Loaders (Tạo map {file_type: BaseLoader_instance})
            supported_loaders_classes = LoaderFactory.get_supported_loaders(self.config.file_types)
            self._loaders: Dict[str, BaseLoader] = {
                file_type: loader_class() 
                for file_type, loader_class in supported_loaders_classes.items()
            }
            logger.info(f"Ingestion service is configured for: {list(self._loaders.keys())}")
            
        except Exception as e:
            logger.critical(f"Failed to build Ingestion components: {e}", exc_info=True)
            raise RuntimeError("RAGIngestionService initialization failed.") from e


    async def _async_load_and_chunk_single_file(self, file_path: str, file_type: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Hardening 2: Loads, chunks, and prepares data for a single file asynchronously.
        """
        if file_type not in self._loaders:
            logger.warning(f"No loader available for file type: {file_type}. Skipping file: {file_path}")
            return []

        loader = self._loaders[file_type]
        
        try:
            # 1. Data Loading (Async I/O)
            loaded_data = await loader.async_load(file_path_or_data=file_path)
            raw_text = loaded_data['content']
            initial_metadata = loaded_data['metadata']
            
            # 2. Chunking (CPU-bound, synchronous, nhưng được điều phối bởi async outer loop)
            chunks_with_metadata = self._chunker.chunk(raw_text, initial_metadata)
            
            return chunks_with_metadata
        except Exception as e:
            logger.error(f"Failed processing file {file_path} with type {file_type}: {e}", exc_info=True)
            # Hardening: Bỏ qua file lỗi và tiếp tục các file khác
            return []


    async def _async_create_embeddings_batch(self, chunks_with_metadata: List[Tuple[str, Dict[str, Any]]]) -> List[Tuple[np.ndarray, Dict[str, Any]]]:
        """
        Hardening 3: Chạy Embedding song song cho một batch các đoạn văn bản.
        """
        texts = [c[0] for c in chunks_with_metadata]
        metadatas = [c[1] for c in chunks_with_metadata]
        
        if not texts: return []
        
        try:
            # GỌI ASYNC EMBED SONG SONG (Sử dụng BaseLLM.async_embed)
            embedding_tasks = [self.embedding_llm.async_embed(text) for text in texts]
            # asyncio.gather đảm bảo hiệu suất cao
            vectors_list = await asyncio.gather(*embedding_tasks)
            
            # Kết quả (vector, metadata)
            final_data = []
            for vector, metadata in zip(vectors_list, metadatas):
                # Hardening: Đảm bảo vector dim khớp với config
                if len(vector) != self.config.embedding_model.vector_dim:
                    logger.error("Generated vector dimension does not match configured dimension. Skipping.")
                    continue
                
                final_data.append((np.array(vector), metadata))
            
            return final_data
            
        except Exception as e:
            logger.error(f"Failed to create embeddings batch: {e}")
            # Propagate error up for Orchestrator to handle
            raise GenAIFactoryError(f"Embedding service failed during batch processing: {e}")


    async def async_run_ingestion_pipeline(self, source_uri: str) -> List[Tuple[np.ndarray, Dict[str, Any]]]:
        """
        Điều phối toàn bộ quy trình Indexing: Load -> Chunk -> Embed -> Output.
        """
        logger.info(f"RAG Ingestion: Starting pipeline for {source_uri}")

        # MOCK/GIẢ LẬP: Lấy danh sách tệp cần xử lý từ URI
        # Trong thực tế, đây là nơi ta dùng s3 client async hoặc os.walk async
        mock_file_list = [
            (os.path.join(source_uri, "policy_1.pdf"), "pdf"),
            (os.path.join(source_uri, "guide_1.docx"), "docx"),
            (os.path.join(source_uri, "unsupported.xlsx"), "xlsx"), # Sẽ bị bỏ qua
        ]
        
        # Lọc các file theo cấu hình
        files_to_process = [(p, t) for p, t in mock_file_list if t in self.config.file_types]

        if not files_to_process:
            logger.warning("No files found or none matched the configured file types.")
            return []

        # 1. Load và Chunk (Chạy song song)
        load_chunk_tasks = []
        for file_path, file_type in files_to_process:
            load_chunk_tasks.append(
                self._async_load_and_chunk_single_file(file_path, file_type)
            )

        # Chạy Load và Chunk BẤT ĐỒNG BỘ cho tất cả các file
        results_list_of_lists = await asyncio.gather(*load_chunk_tasks)
        
        # 2. Làm phẳng danh sách chunks và metadata
        all_chunks_for_embedding = list(itertools.chain.from_iterable(results_list_of_lists))
        
        if not all_chunks_for_embedding:
            logger.warning("Load and Chunk stage resulted in zero chunks. Check loaders/files.")
            return []

        # 3. Embedding Creation (Batch processing)
        logger.info(f"Generated {len(all_chunks_for_embedding)} chunks. Starting batch embedding...")
        return await self._async_create_embeddings_batch(all_chunks_for_embedding)