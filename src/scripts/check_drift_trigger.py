# src/scripts/check_drift_trigger.py

import sys
import argparse
import logging
import asyncio
from typing import Dict, Any, Optional

# Import components
from src.domain_models.genai_assistant.utils.drift_monitor import DriftMonitor 
from shared_libs.exceptions import GenAIFactoryError
from domain_models.genai_assistant.configs.config_loader import ConfigLoader

# --- Cấu hình Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DRIFT_CHECKER_RUNNER")

# Giả định: Hàm để kích hoạt Airflow/K8s Job
def trigger_retraining_workflow(model_name: str, reason: str):
    """
    Placeholder: Kích hoạt một job huấn luyện mới (gọi API của MLOps Orchestrator).
    """
    logger.critical(f"!!! RETRAINING REQUIRED !!! Reason: {reason}. Triggering MLOps Job for {model_name}.")
    # Trong production: sử dụng requests.post() để gọi Airflow REST API hoặc gửi sự kiện Kafka
    return True

def parse_args() -> Dict[str, Any]:
    """Parses command line arguments for the drift check job."""
    parser = argparse.ArgumentParser(description="Checks for Data/Concept Drift and triggers retraining if necessary.")
    parser.add_argument("--model-name", type=str, default="genai-assistant", help="Name of the model being monitored.")
    parser.add_argument("--config-path", type=str, default="configs/mlops/drift_monitor_config.yaml", help="Path to the Drift Monitor YAML configuration file.")
    return vars(parser.parse_args())

def main():
    args = parse_args()

    try:
        # 1. Tải và Xác thực cấu hình
        config_loader = ConfigLoader()
        drift_conf_data = config_loader.load_yaml(args['config-path'])
        drift_conf = drift_conf_data['DRIFT_MONITOR_CONFIG']
        
        # 2. Khởi tạo DriftMonitor với các tham số đã cấu hình
        drift_monitor = DriftMonitor(
            monitoring_config=drift_conf,
            threshold=drift_conf['data_drift_threshold']
        )
        
        logger.info(f"Starting Drift Check for model: {args['model-name']}")
        
        # 3. Chạy logic kiểm tra Drift (giả định đây là phương thức chính)
        # DriftMonitor.analyze_production_data() sẽ kết nối với log store để phân tích
        drift_status, drift_score, reason = drift_monitor.analyze_production_data()
        
        # 4. Quyết định MLOps (HARDENING: Quality Gate Trigger)
        if drift_status == True:
            logger.warning(f"MODEL DRIFT DETECTED! Score {drift_score} > Threshold {drift_conf['data_drift_threshold']}. Reason: {reason}")
            
            # 5. Kích hoạt workflow tái huấn luyện
            trigger_retraining_workflow(args['model-name'], reason)
            
            logger.info("Retraining trigger signal sent successfully.")
        else:
            logger.info(f"Drift check passed. Score: {drift_score}. Model is stable.")

    except GenAIFactoryError as e:
        logger.critical(f"Drift Check failed due to Factory error: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unhandled system failure during Drift Check: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()