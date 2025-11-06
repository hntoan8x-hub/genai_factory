# ----------------------------
# 🔹 ETL ROLE IMAGE (Cleanup, Governance, Monitoring Batch)
# ----------------------------

# 1. Kế thừa từ Base Image đã Hardened
FROM hardened_base AS etl_stage 

# 2. Copy Python Packages cần thiết (pandas, requests, prometheus_client)
COPY --from=dependency_builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# 3. ENTRYPOINT: Chạy job dọn dẹp hoặc kiểm tra health (CronJob)
# Chọn một script làm mặc định (ví dụ: Cleanup, vì nó chạy định kỳ)
ENTRYPOINT ["python3", "scripts/cleanup_old_artifacts.py"]
# NOTE: Lệnh này thường được override bằng K8s CronJob để chạy monitor_service_health.py