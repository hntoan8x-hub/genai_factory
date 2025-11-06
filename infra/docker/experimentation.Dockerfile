# ----------------------------
# 🔹 EXPERIMENTATION ROLE IMAGE (Testing, Validation, Deployment)
# ----------------------------

# 1. Kế thừa từ Base Image đã Hardened
FROM hardened_base AS experimentation_stage 

# 2. Copy Python Packages cần thiết
# Packages: Thư viện kiểm thử (pytest), client deployment, mlops client
COPY --from=dependency_builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# 3. Chuyên biệt hóa (Nếu cần thêm data/tool đặc biệt cho testing)
# Không cần NLTK, giữ nguyên user non-root

# 4. ENTRYPOINT: Chạy job triển khai (deployment)
ENTRYPOINT ["python3", "scripts/deploy_service.py"]
# NOTE: Lệnh này có thể được override để chạy run_load_test.py hoặc run_canary_rollout.py