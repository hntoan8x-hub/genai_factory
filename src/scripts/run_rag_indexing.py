# src/scripts/run_rag_indexing.py (FINAL INTEGRATION)

import sys
import argparse
import logging
import asyncio
from typing import Dict, Any, List, Tuple
import numpy as np

# Import components cốt lõi
from shared_libs.base.base_llm import BaseLLM
from shared_libs.utils.exceptions import GenAIFactoryError
from domain_models.genai_assistant.configs.config_loader import ConfigLoader
from shared_libs.factory.llm_factory import LLMFactory 

# Import Ingestion & Feature Store Modules
from shared_libs.ingestion.configs.rag_ingestion_config_schema import RAGIngestionConfig 
from shared_libs.ingestion.services.rag_ingestion_service import RAGIngestionService 
from shared_libs.feature_store.orchestrator.feature_store_orchestrator import FeatureStoreOrchestrator 
from shared_libs.feature_store.configs.feature_store_config_schema import FeatureStoreConfig 

logger = logging.getLogger("RAG_INDEXER_RUNNER")

def parse_args() -> Dict[str, Any]:
    """Parses command line arguments for the RAG indexing job."""
    parser = argparse.ArgumentParser(description="Runs the RAG Indexing Pipeline to update Vector Database.")
    # Sử dụng config cho toàn bộ Ingestion Layer
    parser.add_argument("--ingestion-config-path", type=str, default="configs/ingestion/default_ingestion.yaml", help="Path to the RAG Ingestion Config YAML.")
    # Sử dụng config cho Feature Store Layer
    parser.add_argument("--feature-store-config-path", type=str, default="configs/feature_store/default_config.yaml", help="Path to the Feature Store Config YAML.")
    return vars(parser.parse_args())


async def async_main_indexing(args: Dict[str, Any]):
    """The main asynchronous logic for the RAG Indexing job."""
    
    # 1. Tải và Xác thực Cấu hình (Quality Gate)
    config_loader = ConfigLoader()
    
    # a. Tải Ingestion Config
    ingestion_conf_dict = config_loader.load_yaml(args['ingestion-config-path'])
    ingestion_config: RAGIngestionConfig = RAGIngestionConfig.model_validate(ingestion_conf_dict)
    
    # b. Tải Feature Store Config
    feature_store_conf_dict = config_loader.load_yaml(args['feature-store-config-path'])
    feature_store_config: FeatureStoreConfig = FeatureStoreConfig.model_validate(feature_store_conf_dict)
    
    # HARDENING: Consistency Check (Kiểm tra chéo)
    ingestion_dim = ingestion_config.embedding_model.vector_dim
    store_dim = feature_store_config.vector_store.params.get('vector_dim')
    
    if ingestion_dim != store_dim:
        raise GenAIFactoryError(f"CRITICAL CONFIG MISMATCH: Embedding dimension ({ingestion_dim}) must match Vector Store dimension ({store_dim}).")
        
    # 2. Khởi tạo LLM (Embedding Model)
    llm_conf = config_loader.get_llm_config(ingestion_config.embedding_model.config_key)
    embedding_llm: BaseLLM = LLMFactory.create_llm(llm_conf) 
    
    # 3. Khởi tạo Orchestrators
    # a. Ingestion Service (Load -> Chunk -> Embed)
    ingestion_service = RAGIngestionService(config=ingestion_config, embedding_llm=embedding_llm)
    
    # b. FeatureStore Orchestrator (Write/Index)
    orchestrator = FeatureStoreOrchestrator(config=feature_store_config)
    orchestrator.connect() # Kết nối đến Vector DB

    try:
        # 4. Thực thi Indexing Pipeline (Load -> Chunk -> Embed)
        preprocessed_data = await ingestion_service.async_run_ingestion_pipeline(
            source_uri=ingestion_config.source_uri # Dùng URI từ config đã validated
        )
        
        if not preprocessed_data:
            logger.warning("No data indexed. Ingestion pipeline returned no vectors.")
            return

        # 5. Ghi dữ liệu vào Feature Store (Write/Index)
        vectors_np = np.stack([item[0] for item in preprocessed_data])
        metadatas = [item[1] for item in preprocessed_data]

        logger.info(f"Starting async indexing (writing {vectors_np.shape[0]} vectors to Feature Store)...")
        
        # Hardening: Sử dụng async_add_features của FeatureStoreOrchestrator
        inserted_ids = await orchestrator.async_add_features(
            vectors=vectors_np,
            metadatas=metadatas
        )
        
        # NOTE: Có thể gọi orchestrator.fit_retriever() ở đây nếu Reranker cần huấn luyện
        
        logger.info(f"RAG Indexing Pipeline completed successfully. Total vectors indexed: {len(inserted_ids)}.")

    except Exception as e:
        logger.critical(f"FATAL: RAG Indexing Job failed: {e}", exc_info=True)
        # Re-raise lỗi sau khi dọn dẹp
        raise GenAIFactoryError(f"Indexing job failed: {e}")
    finally:
        orchestrator.disconnect() 


def main():
    args = parse_args()
    try:
        asyncio.run(async_main_indexing(args))
    except Exception as e:
        logger.critical(f"FATAL: Indexing Job terminated: {e}", exc_info=True)
        sys.exit(1) 

if __name__ == "__main__":
    main()