import os
import hashlib
import time

from starlette.responses import JSONResponse, HTMLResponse
from starlette.requests import Request
from pathlib import Path

from .token_handler import TokenHandler
from .config import oauth_config


async def login_page(request: Request) -> HTMLResponse:
    """返回登录页面"""
    try:
        templates_dir = Path(__file__).parent.parent / "templates"
        login_html = templates_dir / "login.html"
        
        with open(login_html, "r", encoding="utf-8") as f:
            content = f.read()
        
        return HTMLResponse(content)
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>错误</h1><p>加载登录页面失败: {str(e)}</p>",
            status_code=500
        )

async def login(request: Request) -> JSONResponse:
    """
    OAuth 2.0密码模式端点
    
    请求格式：
    POST /mcp/auth/login
    Content-Type: application/json
    {
        "grant_type": "password",
        "username": "用户名",
        "password": "密码",
        "client_id": "客户端ID",
        "client_secret": "客户端密钥"
    }
    """
    # 检查 Accept 头部
    accept_header = request.headers.get("accept", "*/*")
    if accept_header != "*/*" and "application/json" not in accept_header:
        return JSONResponse(
            {"error": "not_acceptable", "error_description": "Client must accept application/json response"},
            status_code=406
        )

    try:
        data = await request.json()
        
        # 验证授权类型
        grant_type = data.get("grant_type")
        if grant_type not in oauth_config.GRANT_TYPES:
            return JSONResponse(
                {"error": "unsupported_grant_type"},
                status_code=400
            )
            
        # 验证客户端凭据
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")
        
        if not client_id or not client_secret:
            return JSONResponse(
                {"error": "invalid_client"},
                status_code=401
            )
            
        if client_id != oauth_config.CLIENT_ID or client_secret != oauth_config.CLIENT_SECRET:
            return JSONResponse(
                {"error": "invalid_client"},
                status_code=401
            )
        
        if grant_type == "password":
            username = data.get("username")
            #password = data.get("password")

            encrypted_password = data.get("password")  # 从前端接收的加密密码

            if not username or not encrypted_password:
                return JSONResponse(
                    {"error": "invalid_request", "error_description": "Missing username or password"},
                    status_code=400
                )

            # 获取时间戳和盐值
            timestamp = request.headers.get("X-Timestamp")
            salt = request.headers.get("X-Salt")

            if not timestamp or not salt:
                return JSONResponse(
                    {"error": "invalid_request", "error_description": "Missing security parameters"},
                    status_code=400
                )

            # 验证时间戳是否在有效期内（5分钟）
            try:
                ts = int(timestamp) / 1000  # 转换为秒
                current_time = time.time()
                if current_time - ts > 300:  # 5分钟过期
                    return JSONResponse(
                        {"error": "invalid_request", "error_description": "Request expired"},
                        status_code=400
                    )
            except (ValueError, TypeError):
                return JSONResponse(
                    {"error": "invalid_request", "error_description": "Invalid timestamp"},
                    status_code=400
                )

            # 验证密码
            # 1. 使用与前端相同的加密方式验证
            # 第一次哈希：密码 + 盐
            first_hash = hashlib.sha256((os.getenv("OAUTH_USER_PASSWORD", "admin") + salt).encode()).hexdigest()
            # 第二次哈希：第一次哈希结果 + 时间戳
            expected_hash = hashlib.sha256((first_hash + timestamp).encode()).hexdigest()


            # 这里应该添加实际的用户验证逻辑
            if username == os.getenv("OAUTH_USER_NAME", "admin") and encrypted_password == expected_hash :
                # 生成令牌
                access_token, refresh_token, access_expires, refresh_expires = TokenHandler.create_tokens(
                    user_id="1",  # 这里应该是实际的用户ID
                    username=username
                )
                
                # 返回标准的OAuth2.0响应
                return JSONResponse(
                    TokenHandler.create_token_response(
                        access_token,
                        refresh_token,
                        access_expires,
                        refresh_expires
                    )
                )
            
            return JSONResponse(
                {"error": "invalid_grant"},
                status_code=401
            )
            
        elif grant_type == "refresh_token":
            refresh_token = data.get("refresh_token")
            if not refresh_token:
                return JSONResponse(
                    {"error": "invalid_request"},
                    status_code=400
                )
                
            # 验证刷新令牌
            payload = TokenHandler.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh_token":
                return JSONResponse(
                    {"error": "invalid_grant"},
                    status_code=401
                )
                
            # 生成新的令牌
            access_token, new_refresh_token, access_expires, refresh_expires = TokenHandler.create_tokens(
                user_id=payload["sub"],
                username=payload["username"]
            )
            
            return JSONResponse(
                TokenHandler.create_token_response(
                    access_token,
                    new_refresh_token,
                    access_expires,
                    refresh_expires
                )
            )
    
    except Exception as e:
        return JSONResponse(
            {"error": "server_error", "error_description": str(e)},
            status_code=500
        ) 