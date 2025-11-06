# src/scripts/run_load_test.py (FINAL PRODUCTION CODE)

import sys
import argparse
import logging
import asyncio
from typing import Dict, Any, Optional

# Import Factory và Exception
from shared_libs.exceptions import GenAIFactoryError 
from domain_models.genai_assistant.configs.config_loader import ConfigLoader

# Hardening: Import Schema và Adapter
from shared_libs.testing.configs.load_test_schema import LoadTestConfigSchema
from shared_libs.testing.implementations.custom_async_client import CustomAsyncPerformanceClient 
from pydantic import ValidationError # Cần bắt lỗi Pydantic

# --- Cấu hình Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LOAD_TEST_RUNNER")

def parse_args() -> Dict[str, Any]:
    """Parses command line arguments for the deployment job."""
    parser = argparse.ArgumentParser(description="Runs Load Testing against a newly deployed endpoint.")
    parser.add_argument("--endpoint-url", type=str, required=True, help="URL of the new GenAI Assistant endpoint.")
    parser.add_argument("--test-config-path", type=str, default="configs/testing/load_test_config.yaml", help="Path to load test configuration.")
    parser.add_argument("--model-version", type=str, required=True, help="Version tag being tested.")
    return vars(parser.parse_args())

async def main_async():
    args = parse_args()
    
    try:
        # 1. Tải và Xác thực cấu hình tải (CRITICAL QUALITY GATE)
        config_loader = ConfigLoader()
        test_conf_data = config_loader.load_yaml(args['test-config-path'])['LOAD_TEST_CONFIG']
        
        # Hardening: Xác thực cấu hình bằng LoadTestConfigSchema
        test_conf: LoadTestConfigSchema = LoadTestConfigSchema.model_validate(test_conf_data)

        url = args['endpoint_url']
        
        logger.info(f"Starting Load Test on {url} at {test_conf.target_qps} QPS for {test_conf.duration_seconds}s.")
        
        # 2. Khởi tạo và chạy Client (Sử dụng Adapter đã Hardening)
        client = CustomAsyncPerformanceClient(url, test_conf.model_dump()) # Truyền config đã validate
        results = await client.run_test()
        
        # 3. Quality Gate: Kiểm tra SLA (CRITICAL HARDENING)
        passed = True
        
        p95_latency = results['p95_latency_ms']
        error_rate = results['error_rate']
        
        if p95_latency > test_conf.max_p95_latency_ms:
            logger.critical(f"FAIL: P95 Latency ({p95_latency}ms) exceeded SLA ({test_conf.max_p95_latency_ms}ms).")
            passed = False
        
        if error_rate > test_conf.max_error_rate:
            logger.critical(f"FAIL: Error Rate ({error_rate * 100:.2f}%) exceeded threshold ({test_conf.max_error_rate * 100}%).")
            passed = False
            
        # 4. Báo cáo
        if passed:
            logger.info(f"SUCCESS: Model {args['model-version']} passed Load Test. P95 Latency: {p95_latency}ms, Error Rate: {error_rate * 100:.2f}%.")
        else:
            logger.critical(f"LOAD TEST FAILED. Deployment for {args['model-version']} is UNSTABLE.")
            sys.exit(1) # Báo lỗi để Rollout Job (run_canary_rollout) dừng lại

    except ValidationError as ve:
        logger.critical(f"FATAL CONFIGURATION ERROR: Load Test schema validation failed: {ve}")
        sys.exit(1)
    except GenAIFactoryError as e:
        logger.critical(f"Load Test failed due to Factory error: {e}", exc_info=True)
        sys.exit(1) 
    except Exception as e:
        logger.critical(f"Unhandled critical system failure during Load Test: {e}", exc_info=True)
        sys.exit(1)

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()