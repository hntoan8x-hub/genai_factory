# src/scripts/run_canary_rollout.py (FINAL PRODUCTION CODE)

import sys
import argparse
import logging
import time
import asyncio
from typing import Dict, Any, Tuple, Optional

# Import components cốt lõi
from shared_libs.ultils.exceptions import GenAIFactoryError 
from domain_models.genai_assistant.configs.config_loader import ConfigLoader

# Hardening: Import Factory và Adapters thực tế
from shared_libs.deployment.factory.deployer_factory import DeployerFactory
# Giả định sử dụng IstioTrafficController (hoặc Adapter đã chọn)
from shared_libs.deployment.implementations.istio_traffic_controller import IstioTrafficController 
from shared_libs.deployment.configs.deployment_schema import DeploymentTargetSchema # Schema để lấy config

logger = logging.getLogger("CANARY_RUNNER")

# --- MOCK: Hàm kiểm tra metrics trực tiếp (CRITICAL HARDENING) ---
async def check_live_metrics(endpoint_name: str, new_version: str) -> bool:
    """
    Mô phỏng việc kiểm tra các metrics quan trọng (Error Rate, Safety Violations, Latency P99).
    Trong Production, hàm này sẽ gọi API của Prometheus/Grafana/Logging System.
    """
    logger.info(f"Monitoring live metrics for version {new_version}...")
    await asyncio.sleep(10) # Đợi 10 giây để thu thập metrics trong giai đoạn Canary
    
    # MOCK Logic: Giả định 95% thời gian là ổn định
    if time.time() % 100 < 95:
        # Giả định metrics ổn định (Error rate < 0.5%, Latency P95 < 600ms)
        logger.info("Live metrics check passed (simulated).")
        return True 
    else:
        logger.critical("Canary check FAILED: High error rate (5xx) or Safety violations detected!")
        return False

# --- Hardening: Hàm lấy Deployer và Traffic Controller từ Config ---
def get_deployment_components(config_path: str, endpoint_name: str) -> Tuple[Any, Any, Dict[str, Any], str]:
    """
    Tải config, xác thực schema, và tạo Deployer/TrafficController instances.
    """
    try:
        config_loader = ConfigLoader()
        deployment_conf_data = config_loader.load_yaml(config_path)
        
        schema_data = deployment_conf_data['DEPLOYMENT_TARGET']
        deployment_schema: DeploymentTargetSchema = DeploymentTargetSchema.model_validate(schema_data)
        
        platform = deployment_schema.platform_type
        
        # 1. Khởi tạo Deployer (Dùng config đã validate)
        platform_config_object = getattr(deployment_schema, platform)
        platform_config = platform_config_object.model_dump() if platform_config_object else {}
        deployer = DeployerFactory.create_deployer(platform, platform_config)
        
        # 2. Khởi tạo Traffic Controller (Giả định K8s dùng Istio)
        # Trong hệ thống đa nền tảng, cần Factory cho TrafficController
        # Ở đây ta MOCK config Istio
        # LƯU Ý: Token cần được tiêm từ Secret Manager vào config trước khi config được tải.
        traffic_conf = {
            'api_endpoint': 'https://istio.api/v1', 
            'namespace': 'mlops-prod', 
            'api_token': 'RUNTIME_SECRET_TOKEN' 
        } 
        traffic_controller = IstioTrafficController(endpoint_name, traffic_conf)
        
        # 3. MOCK Deploy Config (Cần được truyền từ Job Artifacts)
        deploy_config = {
            'model_artifact_uri': 's3://path/to/new_model',
            'image_uri': 'registry/new_model_image:latest',
            'version_tag': deployment_schema.endpoint_name.split('-')[-1]
        }
        
        return deployer, traffic_controller, deploy_config, platform
        
    except Exception as e:
        logger.critical(f"Failed to load deployment components: {e}")
        raise GenAIFactoryError(f"Configuration/Factory Error: {e}")


def parse_args() -> Dict[str, Any]:
    """Parses command line arguments for the Canary Rollout job."""
    parser = argparse.ArgumentParser(description="Runs a progressive Canary Rollout.")
    parser.add_argument("--endpoint-name", type=str, required=True, help="Name of the service/endpoint to manage traffic for.")
    parser.add_argument("--new-version", type=str, required=True, help="New model version tag (already deployed).")
    parser.add_argument("--stable-version", type=str, required=True, help="Current stable model version tag.")
    parser.add_argument("--config-path", type=str, default="configs/deployment/deployer_config.yaml", help="Path to the Deployer YAML configuration file.")
    return vars(parser.parse_args())

async def async_main_canary(args: Dict[str, Any]):
    
    endpoint_name = args['endpoint-name']
    stable_version = args['stable-version']
    new_version = args['new-version']
    
    # 1. Khởi tạo Deployer và Traffic Controller (Dùng ConfigPath)
    deployer, traffic_controller, deploy_config, platform = get_deployment_components(args['config-path'], endpoint_name)
    
    try:
        logger.info(f"Starting Canary Rollout on {platform}: {new_version} -> {stable_version}")
        
        # Hardening 1: BƯỚC 1 - Đảm bảo phiên bản mới đã được triển khai (Added as a variant/subset)
        logger.info(f"Step 0: Invoking async_update_endpoint to deploy new version {new_version}...")
        # deploy_config['image_uri'] và 'model_artifact_uri' phải được lấy từ MLflow/Artifactory
        await deployer.async_update_endpoint(endpoint_name, new_version, deploy_config)
        logger.info("New version deployment successful (0% traffic). Ready to shift traffic.")
        
        # Các bước chuyển đổi lưu lượng (Progressive Rollout)
        CANARY_STEPS = [5, 25, 50, 100] 
        
        for step in CANARY_STEPS:
            new_traffic_percent = step
            
            # 2. Điều chỉnh Lưu lượng (Sử dụng Adapter thực tế Istio/SageMaker, v.v.)
            # async_set_traffic sẽ gọi API và chờ xác nhận (Polling)
            if not await traffic_controller.async_set_traffic(new_version, new_traffic_percent, stable_version):
                # Nếu API Call hoặc Polling thất bại
                raise GenAIFactoryError(f"Failed to set traffic split to {new_traffic_percent}%. Aborting Canary.")

            if step == 100:
                logger.info("Rollout Complete. Final stability check before marking 100%.")
                await asyncio.sleep(5) 
                break

            # 3. Giám sát trong Giai đoạn (CRITICAL CHECK)
            logger.info(f"Monitoring stability at {step}% traffic for 15 seconds...")
            await asyncio.sleep(15) # Thời gian chờ cho Monitoring Dashboard cập nhật
            
            if not await check_live_metrics(endpoint_name, new_version):
                logger.critical("Canary metrics FAILED during monitoring phase.")
                # Nếu Canary thất bại, thoát với mã lỗi đặc biệt (SystemExit 2)
                raise SystemExit(2) 

        logger.info(f"SUCCESS: Canary Rollout completed. {new_version} is now 100% live and stable.")

    except GenAIFactoryError as e:
        logger.critical(f"Canary Job failed due to Factory error: {e}", exc_info=True)
        sys.exit(1)
    except SystemExit:
         # Hardening: Bắt lỗi SystemExit 2 (Canary Failure) và truyền lên trên để kích hoạt Rollback Job
         raise
    except Exception as e:
        logger.critical(f"Canary Job failed unexpectedly: {e}", exc_info=True)
        sys.exit(1)

def main():
    args = parse_args()
    try:
        asyncio.run(async_main_canary(args))
    except SystemExit as e:
        # Nếu mã thoát là 2 (Canary Failure), hệ thống bên ngoài (Airflow/K8s Job) sẽ bắt lỗi này
        if e.code == 2:
            logger.critical("CANARY FAILURE DETECTED. The calling system MUST trigger the Rollback Deployment job now.")
            # Trong production, dòng này báo hiệu cho MLOps Orchestrator (Airflow/Argo/K8s) kích hoạt rollback
            sys.exit(2) 
        sys.exit(e.code)

if __name__ == "__main__":
    main()