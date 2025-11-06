#dags/rag_indexing_dag.py
# DAG 1: Phục vụ Tri thức (RAG Indexing Workflow)

from __future__ import annotations
import pendulum
from airflow.models.dag import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import timedelta

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
    dag_id="rag_indexing_workflow",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    schedule="0 3 * * *", # Chạy hàng ngày lúc 03:00 sáng
    catchup=False,
    default_args={
        "owner": "mlops-team",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        "execution_timeout": timedelta(hours=3)
    },
    tags=["genai", "rag", "indexing"],
) as dag:

    # 1. Tác vụ: Kiểm tra Sức khỏe Vector DB (Smoke Test)
    # Đảm bảo DB đang hoạt động trước khi gửi I/O nặng
    check_db_health = KubernetesPodOperator(
        task_id="check_db_health",
        name="check-db-health",
        image="your-registry/genai-factory:etl-v1.0", # Dùng ETL Role cho job nhẹ
        cmds=["python3"],
        arguments=["scripts/monitor_service_health.py", "--config-path", "configs/monitoring/db_health_check.yaml"],
        **K8S_FULL_CONFIG
    )

    # 2. Tác vụ: Chạy Indexing Job (Load -> Chunk -> Embed -> Write DB)
    # Sử dụng TRAINER Role (có đủ tài nguyên và thư viện ML/FAISS)
    run_indexing = KubernetesPodOperator(
        task_id="run_rag_indexing_job",
        name="rag-indexing-job",
        image="your-registry/genai-factory:trainer-v1.0", # Sử dụng TRAINER Role
        # Dùng ENTRYPOINT mặc định (scripts/run_rag_indexing.py)
        arguments=[
            "--ingestion-config-path", "$(INGESTION_CONFIG_PATH)",
            "--feature-store-config-path", "$(FEATURE_STORE_CONFIG_PATH)"
        ],
        # Đảm bảo cấu hình tài nguyên cho I/O nặng
        container_resources={
            "request_cpu": "2000m", 
            "limit_cpu": "4000m", 
            "limit_memory": "8Gi"
        },
        **K8S_FULL_CONFIG
    )

    # 3. Tác vụ: Dọn dẹp Artifact (Cost Governance)
    # Dùng ETL Role để dọn dẹp các artifact/index cũ (Cost Hardening)
    cleanup_old_data = KubernetesPodOperator(
        task_id="cleanup_old_artifacts",
        name="cleanup-job",
        image="your-registry/genai-factory:etl-v1.0",
        cmds=["python3"],
        arguments=["scripts/cleanup_old_artifacts.py", "--config-path", "configs/governance/cleanup_config.yaml"],
        **K8S_FULL_CONFIG
    )

    # Định nghĩa Luồng (Flow): Check Health -> Index -> Cleanup
    check_db_health >> run_indexing >> cleanup_old_data