import webbrowser
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Optional, Dict, Set
import os
import time

from .token_handler import TokenHandler


class OAuthMiddleware(BaseHTTPMiddleware):
    """OAuth认证中间件"""
    
    # 类级别的弹窗记录，确保所有实例共享
    _global_popup_time: float = 0
    _popup_cooldown: float = 5  # 冷却时间（秒）
    
    def __init__(self, app, exclude_paths: Optional[list[str]] = None):
        """
        初始化中间件
        
        Args:
            app: Starlette应用实例
            exclude_paths: 不需要认证的路径列表
        """
        super().__init__(app)
        # 默认排除路径：登录相关页面和资源
        default_exclude_paths = [
            "/login",                    # 登录页面
            "/mcp/auth/login",          # 登录API
            "/favicon.ico",             # 网站图标
            "/static",                  # 静态资源
        ]
        self.exclude_paths = exclude_paths or default_exclude_paths
        self.login_url = os.getenv("MCP_LOGIN_URL", "http://localhost:3000/login")
    
    def _is_excluded_path(self, path: str) -> bool:
        """
        检查路径是否在排除列表中
        
        Args:
            path: 请求路径
            
        Returns:
            bool: 是否排除认证
        """
        return any(
            path == excluded or path.startswith(f"{excluded}/")
            for excluded in self.exclude_paths
        )
    
    @classmethod
    def _should_show_popup(cls) -> bool:
        """
        判断是否需要显示弹窗
        
        Returns:
            bool: 是否需要显示弹窗
        """
        current_time = time.time()
        
        # 检查是否在冷却期内
        if current_time - cls._global_popup_time > cls._popup_cooldown:
            cls._global_popup_time = current_time
            return True
        return False
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个处理函数
        """
        # 检查是否需要跳过认证
        if self._is_excluded_path(request.url.path):
            return await call_next(request)
            
        # 获取认证头
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # 只在需要时弹出登录框，并且不是API请求时
            if (not request.url.path.startswith("/api/") and 
                not request.headers.get("accept", "").startswith("application/json") and
                self._should_show_popup()):
                webbrowser.open(self.login_url)
            
            return JSONResponse(
                {"error": "invalid_request", "error_description": "Missing authorization header"},
                status_code=401
            )
            
        # 验证token格式
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                {"error": "invalid_request", "error_description": "Invalid authorization header format"},
                status_code=401
            )
            
        token = parts[1]
        
        # 验证token
        payload = TokenHandler.verify_token(token)
        if not payload:
            return JSONResponse(
                {"error": "invalid_token", "error_description": "Token is invalid or expired"},
                status_code=401
            )
            
        # 检查token类型
        if payload.get("type") != "access_token":
            return JSONResponse(
                {"error": "invalid_token", "error_description": "Invalid token type"},
                status_code=401
            )
            
        # 将用户信息添加到请求对象
        request.state.user = {
            "id": payload["sub"],
            "username": payload["username"]
        }
        
        return await call_next(request) 