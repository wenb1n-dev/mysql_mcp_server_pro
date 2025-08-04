import os
from dotenv import load_dotenv

def get_db_config():
    """从环境变量获取数据库配置信息

    返回:
        dict: 包含数据库连接所需的配置信息
        - host: 数据库主机地址
        - port: 数据库端口
        - user: 数据库用户名
        - password: 数据库密码
        - database: 数据库名称
        - role: 数据库角色权限

    异常:
        ValueError: 当必需的配置信息缺失时抛出
    """
    # 加载.env文件
    ##load_dotenv()

    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
        "role": os.getenv("MYSQL_ROLE", "readonly"),  # 默认为只读角色
        "pool_size": int(os.getenv("POOL_SIZE", 10)),
        "max_overflow": int(os.getenv("POOL_MAX_OVERFLOW", 20)),
        "pool_recycle": int(os.getenv("POOL_RECYCLE", 3600)),
        "pool_timeout": int(os.getenv("POOL_TIMEOUT", 30))
    }

    if not all([config["user"], config["password"], config["database"]]):
        raise ValueError("缺少必需的数据库配置")

    return config

# 定义角色权限
ROLE_PERMISSIONS = {
    "readonly": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"],  # 只读权限
    "writer": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE"],  # 读写权限
    "admin": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE", 
             "CREATE", "ALTER", "DROP", "TRUNCATE"]  # 管理员权限
}

def get_role_permissions(role: str) -> list:
    """获取指定角色的权限列表
    
    参数:
        role (str): 角色名称
        
    返回:
        list: 该角色允许执行的SQL操作列表
    """
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["readonly"])  # 默认返回只读权限