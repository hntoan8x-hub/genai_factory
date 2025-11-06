# dags/model_drift_retrain_dag.py
# DAG 2: Quản lý Chất lượng Mô hình (Drift & Retraining Workflow)
from __future__ import annotations
import pendulum
from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
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
    dag_id="model_drift_retrain_workflow",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    schedule="0 6 * * *", # Chạy hàng ngày lúc 06:00 sáng
    catchup=False,
    default_args={
        "owner": "ai-governance",
        "retries": 0, # Không retry cho Drift Check
        "execution_timeout": timedelta(hours=6)
    },
    tags=["genai", "mlops", "governance"],
) as dag:

    # 1. Tác vụ: Kiểm tra Drift (Role ETL)
    # Nếu script thoát với mã lỗi 0 (No Drift) -> thành công, dừng DAG
    # Nếu script thoát với mã lỗi > 0 (Drift Detected) -> thất bại, trigger tác vụ tiếp theo (Retrain)
    check_drift = KubernetesPodOperator(
        task_id="check_data_concept_drift",
        name="drift-checker",
        image="your-registry/genai-factory:etl-v1.0",
        cmds=["python3"],
        arguments=["scripts/check_drift_trigger.py", "--model-name", "genai-assistant"],
        trigger_rule="all_done", # Chạy Task Retrain chỉ khi Task này hoàn tất
        **K8S_FULL_CONFIG
    )

    # 2. Tác vụ: Huấn luyện lại mô hình (Role TRAINER)
    # Tác vụ này chỉ được kích hoạt nếu tác vụ check_drift THÀNH CÔNG
    run_finetuning = KubernetesPodOperator(
        task_id="run_finetuning_job",
        name="finetune-job",
        image="your-registry/genai-factory:trainer-v1.0", 
        cmds=["python3"],
        arguments=["scripts/run_finetune_job.py", "--model-version-tag", "drift_retrain_{{ ds_nodash }}"],
        trigger_rule="all_success", # Chỉ chạy nếu Drift Check thành công (nghĩa là script báo thành công, dù có thể logic bên trong báo lỗi)
        **K8S_FULL_CONFIG
    )
    
    # 3. Tác vụ: Trigger Deployment Workflow (Kích hoạt DAG khác)
    # Tác vụ này chỉ chạy nếu Retraining THÀNH CÔNG
    trigger_deployment = TriggerDagRunOperator(
        task_id="trigger_deployment_dag",
        trigger_dag_id="deployment_canary_workflow", # Giả định tên DAG triển khai
        conf={"model_version": "drift_retrain_{{ ds_nodash }}"},
        trigger_rule="all_success",
    )

    # Định nghĩa Luồng (Flow): Drift Check -> Retrain -> Trigger Deployment
    check_drift >> run_finetuning >> trigger_deployment