# dags/deployment_canary_dag.py
# DAG 3: Triển khai An toàn (Canary Rollout & Validation Workflow)

from __future__ import annotations
import pendulum
from airflow.models.dag import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import timedelta
from airflow.operators.bash import BashOperator # Dùng Bash cho các lệnh điều khiển nhanh
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

# Cấu hình chung cho Kubernetes
K8S_FULL_CONFIG = {
    "namespace": "mlops-genai",
    "image_pull_policy": "Always",
    "service_account_name": "airflow-k8s-sa",
    "startup_timeout_seconds": 600, # 10 phút timeout khởi động
    "env_from": [
        {"configMapRef": {"name": "genai-factory-configs"}},
        {"secretRef": {"name": "genai-factory-secrets"}}
    ]
}

with DAG(
    dag_id="deployment_canary_workflow",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    schedule=None, # Chỉ chạy khi được trigger thủ công hoặc bởi DAG khác
    catchup=False,
    default_args={
        "owner": "mlops-deployment",
        "retries": 0, 
        "execution_timeout": timedelta(hours=1)
    },
    tags=["genai", "deployment", "canary"],
) as dag:
    
    # Lấy tham số version mới từ conf (được truyền từ trigger)
    NEW_MODEL_VERSION = "{{ dag_run.conf['model_version'] if dag_run and dag_run.conf and dag_run.conf['model_version'] else 'latest' }}"
    STABLE_MODEL_VERSION = "genai-assistant-v1.0" # Giả định phiên bản ổn định đã biết

    # 1. Tác vụ: Triển khai phiên bản mới (Role EXPERIMENTATION)
    # Triển khai phiên bản mới bên cạnh phiên bản ổn định (nhưng chưa chuyển traffic)
    deploy_new_version = KubernetesPodOperator(
        task_id="deploy_new_version",
        name="deploy-new-version",
        image="your-registry/genai-factory:experimentation-v1.0",
        cmds=["python3"],
        arguments=["scripts/deploy_service.py", "--model-name", "genai-assistant", "--image-uri", "your-registry/genai-factory:inference-{{ NEW_MODEL_VERSION }}"],
        **K8S_FULL_CONFIG
    )

    # 2. Tác vụ: Kiểm thử Tải (Load Test - Role EXPERIMENTATION)
    # Kiểm tra SLA (Latency/Error Rate) trên phiên bản mới
    run_load_test = KubernetesPodOperator(
        task_id="run_load_test_validation",
        name="load-test-job",
        image="your-registry/genai-factory:experimentation-v1.0",
        cmds=["python3"],
        arguments=["scripts/run_load_test.py", "--endpoint-url", "http://{{ NEW_MODEL_VERSION }}-endpoint:80", "--model-version", NEW_MODEL_VERSION],
        **K8S_FULL_CONFIG
    )
    
    # 3. Tác vụ: Canary Rollout & Tự động Rollback (Role EXPERIMENTATION)
    # Tác vụ này chứa logic chuyển traffic từng bước và kiểm tra metrics sống
    canary_rollout = KubernetesPodOperator(
        task_id="run_canary_rollout",
        name="canary-rollout-job",
        image="your-registry/genai-factory:experimentation-v1.0",
        cmds=["python3"],
        arguments=["scripts/run_canary_rollout.py", "--endpoint-name", "genai-assistant-service", 
                   "--new-version", NEW_MODEL_VERSION, "--stable-version", STABLE_MODEL_VERSION],
        # HARDENING: Nếu canary thất bại (SystemExit 2), ta cho phép tác vụ Rollback chạy
        trigger_rule="all_done",
        **K8S_FULL_CONFIG
    )

    # 4. Tác vụ: Rollback nếu Canary thất bại (Luồng khẩn cấp)
    # Tác vụ này chỉ chạy khi Canary Rollout thất bại (SystemExit 2)
    rollback_on_failure = KubernetesPodOperator(
        task_id="rollback_deployment",
        name="rollback-job",
        image="your-registry/genai-factory:experimentation-v1.0",
        cmds=["python3"],
        arguments=["scripts/rollback_deployment.py", "--endpoint-name", "genai-assistant-service", 
                   "--stable-version", STABLE_MODEL_VERSION],
        # CRITICAL: Chỉ chạy Rollback nếu tác vụ trước đó thất bại
        trigger_rule="one_failed", 
        **K8S_FULL_CONFIG
    )


    # Định nghĩa Luồng (Flow): Deploy -> Load Test -> Canary (thành công) HOẶC Rollback (thất bại)
    deploy_new_version >> run_load_test >> canary_rollout
    canary_rollout >> rollback_on_failure