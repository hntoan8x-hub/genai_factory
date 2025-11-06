# src/scripts/deploy_service.py (FINAL PRODUCTION CODE)

import sys
import argparse
import logging
from typing import Dict, Any

# Import Factory và Exception
from shared_libs.deployment.factory.deployer_factory import DeployerFactory 
from shared_libs.exceptions import GenAIFactoryError 
from domain_models.genai_assistant.configs.config_loader import ConfigLoader

# Hardening: Import Schema cho Quality Gate
from shared_libs.deployment.configs.deployment_schema import DeploymentTargetSchema 

# --- Cấu hình Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DEPLOYMENT_RUNNER")

def parse_args() -> Dict[str, Any]:
    """Parses command line arguments for the deployment job."""
    parser = argparse.ArgumentParser(description="Deploys a GenAI model artifact to a specific platform.")
    parser.add_argument("--model-name", type=str, required=True, help="Name of the model/endpoint (e.g., genai-assistant-v2).")
    parser.add_argument("--artifact-uri", type=str, required=True, help="URI to the model artifact (MLflow, S3).")
    parser.add_argument("--image-uri", type=str, required=True, help="Container image URI for the deployment.")
    parser.add_argument("--config-path", type=str, default="configs/deployment/deployer_config.yaml", help="Path to the Deployer YAML configuration file.")
    return vars(parser.parse_args())

def main():
    args = parse_args()
    
    try:
        # 1. Tải cấu hình thô
        config_loader = ConfigLoader()
        deployment_conf_data = config_loader.load_yaml(args['config-path'])
        
        # 2. Xác thực và Phân tích cấu hình (CRITICAL QUALITY GATE)
        schema_data = deployment_conf_data['DEPLOYMENT_TARGET']
        # Sử dụng Pydantic/Schema để xác thực dữ liệu đầu vào
        deployment_schema: DeploymentTargetSchema = DeploymentTargetSchema.model_validate(schema_data)
        
        platform = deployment_schema.platform_type
        endpoint_name = deployment_schema.endpoint_name

        # Lấy Config cụ thể cho nền tảng (đã được validate)
        # Sử dụng getattr() để lấy config object tương ứng (e.g., schema.kubernetes, schema.aws)
        platform_config_object = getattr(deployment_schema, platform)
        
        # Chuyển Pydantic model thành Dict để truyền vào Deployer Factory
        if platform_config_object:
            platform_config = platform_config_object.model_dump() 
        else:
            platform_config = {}

        # 3. Sử dụng Deployer Factory
        logger.info(f"🏭 Creating Deployer for platform: {platform}")
        deployer = DeployerFactory.create_deployer(platform, platform_config)
        
        # 4. Tạo Deployment Config chung
        # Hardening: Thêm version tag vào config để Deployer sử dụng
        version_tag = args['model-name'].split('-')[-1] # Ví dụ: genai-assistant-v1.2 -> v1.2
        
        deploy_config = {
            "image_uri": args['image-uri'],
            "model_artifact_uri": args['artifact-uri'],
            "version_tag": version_tag,
            # Có thể thêm các tham số như canary_enabled, initial_traffic, v.v.
        }
        
        logger.info(f"🚀 Deploying model {args['model-name']} (Tag: {version_tag}) to endpoint: {endpoint_name}")
        
        # 5. Kích hoạt triển khai
        # deploy_model() sẽ chờ cho Endpoint Ready (Quality Gate)
        endpoint_id = deployer.deploy_model(
            model_name=endpoint_name,
            model_artifact_uri=args['artifact-uri'],
            deploy_config=deploy_config
        )
        
        logger.info(f"✅ Deployment successful and Endpoint is READY. Endpoint ID: {endpoint_id}")

    except DeploymentTargetSchema.ValidationError as ve:
        # Xử lý lỗi xác thực cấu hình (Pydantic Error)
        logger.critical(f"FATAL CONFIGURATION ERROR: Deployment schema validation failed: {ve}")
        sys.exit(1)
    except GenAIFactoryError as e:
        logger.error(f"Deployment failed due to Factory/Deployment error: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unhandled critical deployment failure: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()