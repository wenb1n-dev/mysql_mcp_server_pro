from datetime import datetime, timedelta
import jwt
from typing import Dict, Optional, Tuple

from ..oauth import oauth_config


class TokenHandler:
    @staticmethod
    def create_tokens(user_id: str, username: str) -> Tuple[str, str, datetime, datetime]:
        """
        创建访问令牌和刷新令牌
        
        Args:
            user_id: 用户ID
            username: 用户名
            
        Returns:
            Tuple[str, str, datetime, datetime]: (访问令牌, 刷新令牌, 访问令牌过期时间, 刷新令牌过期时间)
        """
        # 计算过期时间
        access_token_expires = datetime.utcnow() + timedelta(minutes=oauth_config.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = datetime.utcnow() + timedelta(days=oauth_config.REFRESH_TOKEN_EXPIRE_DAYS)
        
        # 访问令牌数据
        access_token_data = {
            "sub": str(user_id),  # subject (用户ID)
            "username": username,
            "type": "access_token",
            "exp": access_token_expires,
            "iat": datetime.utcnow()
        }
        
        # 刷新令牌数据
        refresh_token_data = {
            "sub": str(user_id),
            "username": username,
            "type": "refresh_token",
            "exp": refresh_token_expires,
            "iat": datetime.utcnow()
        }
        
        # 生成令牌
        access_token = jwt.encode(
            access_token_data,
            oauth_config.TOKEN_SECRET_KEY,
            algorithm=oauth_config.TOKEN_ALGORITHM
        )
        
        refresh_token = jwt.encode(
            refresh_token_data,
            oauth_config.TOKEN_SECRET_KEY,
            algorithm=oauth_config.TOKEN_ALGORITHM
        )
        
        return access_token, refresh_token, access_token_expires, refresh_token_expires
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """
        验证令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict]: 令牌payload，无效则返回None
        """
        try:
            payload = jwt.decode(
                token,
                oauth_config.TOKEN_SECRET_KEY,
                algorithms=[oauth_config.TOKEN_ALGORITHM]
            )
            return payload
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def create_token_response(
        access_token: str,
        refresh_token: str,
        access_token_expires: datetime,
        refresh_token_expires: datetime
    ) -> Dict:
        """
        创建标准的OAuth2.0令牌响应
        
        Args:
            access_token: 访问令牌
            refresh_token: 刷新令牌
            access_token_expires: 访问令牌过期时间
            refresh_token_expires: 刷新令牌过期时间
            
        Returns:
            Dict: OAuth2.0标准令牌响应
        """
        # 转换为北京时间 (UTC+8)
        access_token_expires_beijing = access_token_expires + timedelta(hours=8)
        refresh_token_expires_beijing = refresh_token_expires + timedelta(hours=8)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": oauth_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 秒
            "refresh_token": refresh_token,
            "refresh_token_expires_in": oauth_config.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 秒
            "expire_time": access_token_expires_beijing.strftime("%Y-%m-%d %H:%M:%S (北京时间)"),
            "refresh_token_expire_time": refresh_token_expires_beijing.strftime("%Y-%m-%d %H:%M:%S (北京时间)")
        } 