# src/scripts/rollback_deployment.py (FINAL PRODUCTION CODE)

import sys
import argparse
import logging
import asyncio
from typing import Dict, Any, Tuple

# Import Factory, Exception, và Adapters
from shared_libs.deployment.factory.deployer_factory import DeployerFactory 
from shared_libs.utils.exceptions import GenAIFactoryError, DeploymentError
from domain_models.genai_assistant.configs.config_loader import ConfigLoader

# Hardening: Import Traffic Controller Adapter
from shared_libs.deployment.implementations.istio_traffic_controller import IstioTrafficController 
from shared_libs.deployment.configs.deployment_schema import DeploymentTargetSchema 

logger = logging.getLogger("ROLLBACK_RUNNER")

def parse_args() -> Dict[str, Any]:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Rolls back the deployment to a specified stable version.")
    parser.add_argument("--endpoint-name", type=str, required=True, help="Name of the service/endpoint to rollback.")
    parser.add_argument("--stable-version", type=str, required=True, help="The known stable model version tag to revert to.")
    parser.add_argument("--failed-version", type=str, required=True, help="The version that caused the failure (to be removed from traffic).")
    parser.add_argument("--config-path", type=str, default="configs/deployment/deployer_config.yaml", help="Path to the Deployer YAML configuration file.")
    return vars(parser.parse_args())

# --- Hardening: Hàm lấy Deployer và Traffic Controller từ Config ---
def get_deployment_components(config_path: str, endpoint_name: str) -> Tuple[Any, Any]:
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
        
        # 2. Khởi tạo Traffic Controller (Giả định Istio)
        # LƯU Ý: Traffic config (gồm API Token) phải được tiêm từ Secret Manager
        traffic_conf = {
            'api_endpoint': 'https://istio.api/v1', 
            'namespace': 'mlops-prod', 
            'api_token': 'RUNTIME_SECRET_TOKEN' 
        } 
        traffic_controller = IstioTrafficController(endpoint_name, traffic_conf)
        
        return deployer, traffic_controller
        
    except DeploymentTargetSchema.ValidationError as ve:
        logger.critical(f"FATAL CONFIGURATION ERROR: Schema validation failed: {ve}")
        raise GenAIFactoryError(f"Config validation error: {ve}")
    except Exception as e:
        logger.critical(f"Failed to load deployment components: {e}")
        raise GenAIFactoryError(f"Configuration/Factory Error: {e}")


async def async_main_rollback(args: Dict[str, Any]):
    endpoint_name = args['endpoint-name']
    stable_version = args['stable-version']
    failed_version = args['failed-version']
    
    # 1. Khởi tạo Deployer và Traffic Controller
    deployer, traffic_controller = get_deployment_components(args['config-path'], endpoint_name)
    
    try:
        logger.warning(f"--- INITIATING CRITICAL ROLLBACK ---")
        logger.warning(f"Target: {endpoint_name}. Reverting to stable version: {stable_version}")
        
        # 2. Hardening: Đảm bảo Deployment/Variant ổn định còn hoạt động và có đủ Replica
        # Phương thức này sẽ xử lý logic riêng của từng platform (K8s: scale up, SageMaker: check variant exists)
        deployer.rollback(
            endpoint_name=endpoint_name,
            target_version=stable_version
        )
        logger.info(f"Stable version {stable_version} confirmed to be running and ready for traffic.")
        
        # 3. CRITICAL: Chuyển 100% Lưu lượng về phiên bản ổn định
        # Gọi TrafficController set 0% cho phiên bản thất bại (failed_version)
        if not await traffic_controller.async_set_traffic(
            new_version=failed_version, 
            new_traffic_percentage=0,
            stable_version=stable_version
        ):
             # Hardening: Nếu thất bại, đây là lỗi nghiêm trọng, hệ thống cảnh báo cấp cao
             raise GenAIFactoryError("FATAL: Failed to switch traffic 100% back to stable version (Traffic Controller failure).")
        
        logger.info(f"✅ ROLLBACK SUCCESSFUL. Service {endpoint_name} reverted to stable version {stable_version} (100% traffic).")
        
        # 4. Optional: Kích hoạt Dọn dẹp Tài nguyên (Deferred Deletion)
        # Trong hệ thống Production, việc xóa Deployment/Variant thất bại thường được thực hiện bởi job dọn dẹp riêng
        # logger.info(f"Triggering asynchronous cleanup for failed version: {failed_version}...")
        
    except DeploymentError as e:
        logger.error(f"FATAL: Rollback failed due to Infrastructure/Deployment error: {e}", exc_info=True)
        # Rất quan trọng: Nếu Rollback thất bại, hệ thống cần kích hoạt cảnh báo cấp cao nhất.
        sys.exit(1)
    except GenAIFactoryError as e:
        logger.error(f"FATAL: Rollback failed due to Factory error: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unhandled critical Rollback failure: {e}", exc_info=True)
        sys.exit(1)

def main():
    args = parse_args()
    try:
        # Rollback là quá trình Async vì nó gọi TrafficController API
        asyncio.run(async_main_rollback(args))
    except Exception:
        # Bắt lỗi từ async_main_rollback và exit với mã lỗi (đã được log chi tiết bên trong)
        sys.exit(1)

if __name__ == "__main__":
    main()