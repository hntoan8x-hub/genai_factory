# src/scripts/monitor_service_health.py

import sys
import argparse
import logging
import requests
import asyncio
from typing import Dict, Any, List

# Import Exception
from shared_libs.utils.exceptions import GenAIFactoryError 
from domain_models.genai_assistant.configs.config_loader import ConfigLoader

# --- Cấu hình Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HEALTH_MONITOR_RUNNER")

# Giả định: Hàm gửi cảnh báo đến Slack/PagerDuty
def send_alert(severity: str, message: str):
    """Placeholder: Gửi cảnh báo thực tế đến hệ thống giám sát."""
    print(f"[{severity.upper()} ALERT]: {message}")
    logger.error(f"Alert triggered: {message}")

def parse_args() -> Dict[str, Any]:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Periodically checks core GenAI API endpoints.")
    parser.add_argument("--config-path", type=str, default="configs/monitoring/health_check_config.yaml", help="Path to the Health Check configuration file.")
    return vars(parser.parse_args())

def check_endpoint(url: str, required_status: int = 200, timeout: int = 5) -> bool:
    """Performs a synchronous check on a single HTTP endpoint."""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code != required_status:
            send_alert("HIGH", f"Endpoint {url} returned unexpected status code: {response.status_code}")
            return False
        
        # Kiểm tra nội dung (ví dụ: health check endpoint phải trả về "ok")
        if response.status_code == 200 and 'status' in response.json() and response.json()['status'] == 'ok':
            logger.info(f"Endpoint {url} is healthy.")
            return True
        elif response.status_code == 200:
             logger.info(f"Endpoint {url} returned 200 but content may be degraded.")
             return True # Coi là ổn định nếu status 200

    except requests.exceptions.Timeout:
        send_alert("HIGH", f"Endpoint {url} timed out after {timeout}s.")
        return False
    except requests.exceptions.ConnectionError:
        send_alert("CRITICAL", f"Endpoint {url} connection failed. Service is down.")
        return False
    except Exception as e:
        send_alert("HIGH", f"Unknown error checking {url}: {e}")
        return False
    
    return True

def main():
    args = parse_args()
    overall_success = True
    
    try:
        # 1. Tải cấu hình
        config_loader = ConfigLoader()
        monitor_conf = config_loader.load_yaml(args['config_path'])['HEALTH_CHECK_CONFIG']
        
        target_endpoints = monitor_conf['target_endpoints']
        
        logger.info(f"Starting health check on {len(target_endpoints)} endpoints.")
        
        # 2. Chạy kiểm tra trên tất cả các endpoint (CRITICAL HARDENING)
        for endpoint in target_endpoints:
            if not check_endpoint(endpoint['url'], endpoint.get('status_code', 200)):
                overall_success = False
        
        if overall_success:
            logger.info("All core services reported healthy status.")
        else:
            logger.error("One or more critical endpoints reported failure. Check alerts.")
            sys.exit(1) # Báo lỗi để hệ thống CronJob ghi nhận thất bại

    except GenAIFactoryError as e:
        logger.critical(f"Monitoring failed due to Config/Factory error: {e}", exc_info=True)
        sys.exit(1) 
    except Exception as e:
        logger.critical(f"Unhandled system failure during health check: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()