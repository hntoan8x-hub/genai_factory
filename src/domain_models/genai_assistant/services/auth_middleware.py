# domain_models/genai_assistant/services/auth_middleware.py
import logging
from fastapi import Request, HTTPException, status
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Giả định: Danh sách vai trò được phép gọi các API nhạy cảm
# Ví dụ: Chỉ Admin/Risk Analyst mới được gọi các Tool nhạy cảm như Email/SQL Tool
SENSITIVE_TOOL_ACCESS: Dict[str, List[str]] = {
    "/generate/agent": ["admin", "risk_analyst", "authenticated_users"], # Yêu cầu Agent là nhạy cảm
    "/generate/rag": ["authenticated_users", "guest"],
    "/admin/config": ["admin"], # Chỉ Admin được thay đổi config
}

# Giả định JWT_DECODER là một hàm giải mã và xác thực JWT token
def JWT_DECODER(token: str) -> Dict[str, Any]:
    """Decodes JWT and returns user claims (e.g., user_id, role)."""
    # Trong production: sử dụng thư viện như python-jose để giải mã và xác thực chữ ký
    if token == "GUEST_TOKEN_123":
        return {"user_id": "guest_user", "role": "guest"}
    if token == "ANALYST_TOKEN_456":
        return {"user_id": "hoang_toan", "role": "risk_analyst"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def auth_middleware(request: Request):
    """
    Middleware for Authentication (AuthN) and Role-Based Access Control (AuthZ). (CRITICAL HARDENING)
    """
    
    # 1. Authentication (AuthN) - Xác thực
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header required.")
    
    token = auth_header.split(" ")[1]
    
    try:
        user_claims = JWT_DECODER(token)
        user_role = user_claims.get("role", "guest")
        request.state.user_id = user_claims.get("user_id") # Lưu user_id vào state
        request.state.user_role = user_role
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed.")

    # 2. Authorization (AuthZ) - Phân quyền (RBAC)
    path = request.url.path
    required_roles = SENSITIVE_TOOL_ACCESS.get(path, ["admin"]) # Mặc định chỉ Admin
    
    if user_role not in required_roles:
        logger.warning(f"ACCESS DENIED: User {request.state.user_id} ({user_role}) denied access to {path}.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges.")
    
    # Tiếp tục nếu xác thực và phân quyền thành công