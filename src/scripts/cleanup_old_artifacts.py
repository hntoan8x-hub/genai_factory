# src/scripts/cleanup_old_artifacts.py

import sys
import argparse
import logging
from typing import Dict, Any, List
import time
# Giả định các adapter cho MLflow và S3 tồn tại
from shared_libs.mlops.mlflow_adapter import MLflowClientAdapter 
from shared_libs.infra.storage_client import StorageClient 
from shared_libs.utils.exceptions import GenAIFactoryError 
from domain_models.genai_assistant.configs.config_loader import ConfigLoader

logger = logging.getLogger("ARTIFACT_CLEANUP_RUNNER")

def parse_args() -> Dict[str, Any]:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Cleans up old, unused MLflow artifacts and storage files.")
    parser.add_argument("--config-path", type=str, default="configs/governance/cleanup_config.yaml", help="Path to the Cleanup YAML configuration file.")
    return vars(parser.parse_args())

def get_deployed_models() -> List[str]:
    """Mô phỏng việc lấy danh sách các mô hình đang hoạt động (được triển khai)."""
    # Trong production: Truy vấn Kubernetes/Service Mesh để lấy các version đang phục vụ
    return ["genai-assistant-v1.2", "genai-assistant-v1.3"]

def main():
    args = parse_args()
    
    try:
        # 1. Tải cấu hình
        config_loader = ConfigLoader()
        cleanup_conf = config_loader.load_yaml(args['config_path'])['CLEANUP_GOVERNANCE']
        
        # Ngưỡng thời gian giữ lại (ví dụ: 90 ngày)
        retention_days = cleanup_conf.get('artifact_retention_days', 90)
        retention_seconds = retention_days * 24 * 3600
        cutoff_time = time.time() - retention_seconds
        
        # 2. Khởi tạo Adapters
        mlflow_adapter = MLflowClientAdapter(cleanup_conf['mlflow_uri'])
        storage_client = StorageClient(cleanup_conf['storage_bucket']) # S3/GCS Client
        
        deployed_models = get_deployed_models()
        total_deleted_count = 0
        
        logger.info(f"Starting cleanup for artifacts older than {retention_days} days. Cutoff time: {time.ctime(cutoff_time)}")

        # 3. Quá trình Dọn dẹp Artifact (COST HARDENING)
        all_artifacts = mlflow_adapter.list_all_artifacts() # Giả định trả về list(uri, timestamp, model_name)
        
        for artifact in all_artifacts:
            artifact_uri = artifact['uri']
            model_name = artifact['model_name']
            artifact_timestamp = artifact['timestamp'] # Giả định là epoch time

            # Rule 1: KHÔNG BAO GIỜ xóa mô hình đang được triển khai (CRITICAL SAFETY)
            if model_name in deployed_models:
                continue

            # Rule 2: Xóa mô hình cũ hơn ngưỡng (Retention Policy)
            if artifact_timestamp < cutoff_time:
                logger.warning(f"Deleting old artifact: {model_name} from {time.ctime(artifact_timestamp)}")
                
                # Xóa Artifact trên Storage (S3/GCS)
                storage_client.delete_file(artifact_uri)
                
                # Xóa entry trong MLflow (hoặc unregister)
                mlflow_adapter.delete_artifact_entry(artifact_uri)
                
                total_deleted_count += 1

        logger.info(f"Cleanup completed. Total artifacts deleted: {total_deleted_count}. Savings optimized.")

    except GenAIFactoryError as e:
        logger.critical(f"Artifact Cleanup failed due to Factory error: {e}", exc_info=True)
        sys.exit(1) 
    except Exception as e:
        logger.critical(f"Unhandled system failure during cleanup: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()