"""
SQL执行工具类，使用数据库连接池执行SQL语句
"""

import logging
import re
from enum import Enum
from typing import List, Tuple, Optional, Dict, Any, Set
from dataclasses import dataclass
from contextlib import contextmanager

from mysql.connector import Error as MySQLError

from .database_pool import create_mysql_pool
from ..config import get_db_config, get_role_permissions
from ..exception.exceptions import SQLPermissionError

logger = logging.getLogger(__name__)

class SQLOperation(str, Enum):
    """SQL 操作类型枚举"""
    SELECT = 'SELECT'
    INSERT = 'INSERT'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    CREATE = 'CREATE'
    ALTER = 'ALTER'
    DROP = 'DROP'
    TRUNCATE = 'TRUNCATE'
    SHOW = 'SHOW'
    DESCRIBE = 'DESCRIBE'
    EXPLAIN = 'EXPLAIN'

    @classmethod
    def from_str(cls, value: str) -> 'SQLOperation':
        """从字符串创建 SQLOperation 枚举值

        Args:
            value: SQL 操作字符串

        Returns:
            SQLOperation: 对应的枚举值

        Raises:
            ValueError: 当操作类型不支持时
        """
        try:
            return cls(value.upper())
        except ValueError:
            raise ValueError(f"不支持的SQL操作类型: {value}")

@dataclass
class SQLResult:
    """SQL执行结果"""
    success: bool
    message: str
    columns: Optional[List[str]] = None
    rows: Optional[List[Tuple]] = None
    affected_rows: int = 0


class ExecuteSqlUtil:
    """使用数据库连接池的SQL执行工具类"""

    # SQL操作正则模式
    SQL_COMMENT_PATTERN = re.compile(r'--.*$|/\*.*?\*/', re.MULTILINE | re.DOTALL)

    # 类级别的连接池，确保单例
    _connection_pool = None

    @classmethod
    def create_mysql_pool(cls, db_config: Dict[str, Any]):
        # 提取连接池相关配置
        pool_config = {
            'pool_size': db_config.get('pool_size', 10),
            'max_overflow': db_config.get('max_overflow', 20),
            'pool_recycle': db_config.get('pool_recycle', 3600),
            'pool_timeout': db_config.get('pool_timeout', 30)
        }

        # 提取数据库连接配置
        db_params = {
            'host': db_config.get('host', 'localhost'),
            'port': db_config.get('port', 3306),
            'user': db_config.get('user', 'root'),
            'password': db_config.get('password', ''),
            'database': db_config.get('database', '')
        }

        # 创建MySQL连接池
        cls._connection_pool = create_mysql_pool(
            host=db_params['host'],
            port=db_params['port'],
            user=db_params['user'],
            password=db_params['password'],
            database=db_params['database'],
            pool_size=pool_config['pool_size'],
            max_overflow=pool_config['max_overflow'],
            pool_recycle=pool_config['pool_recycle'],
            pool_timeout=pool_config['pool_timeout']
        )

    @classmethod
    @contextmanager
    def get_db_connection(cls):
        """获取数据库连接的上下文管理器
        
        Yields:
            数据库连接对象
        """
        connection = None
        try:

            if cls._connection_pool is None:
                cls.create_mysql_pool(db_config=get_db_config())

            connection = cls._connection_pool.get_connection()
            yield connection
        except Exception as e:
            logger.error(f"从连接池获取数据库连接失败: {e}")
            raise
        finally:
            if connection is not None:
                try:
                    cls._connection_pool.return_connection(connection)
                except Exception as e:
                    logger.warning(f"归还数据库连接到连接池时出错: {e}")

    def execute_single_statement(self, statement: str) -> SQLResult:
        """执行单条SQL语句
        
        Args:
            statement: SQL语句
            
        Returns:
            SQL执行结果
            
        Raises:
            Exception: 当执行出错时
        """
        try:
            # 检查权限
            operations = self.extract_operations(statement)
            self.check_permissions(operations)

            with ExecuteSqlUtil.get_db_connection() as conn:
                from sqlalchemy import text
                
                # 清理SQL语句并转为大写进行分析
                cleaned_statement = self.clean_sql(statement)
                upper_statement = cleaned_statement.upper().strip()
                
                # 判断语句类型
                is_select = (upper_statement.startswith('SELECT') or 
                           upper_statement.startswith('WITH'))
                
                is_show = upper_statement.startswith('SHOW')
                is_explain = upper_statement.startswith('EXPLAIN')
                is_describe = (upper_statement.startswith('DESCRIBE') or 
                             upper_statement.startswith('DESC '))
                
                # 特殊语句类型（通常返回结果集）
                is_query_type = is_select or is_show or is_explain or is_describe
                
                try:
                    # 执行SQL语句
                    result = conn.execute(text(statement))
                    
                    # 根据语句类型处理结果
                    if is_query_type:
                        # 查询类语句（SELECT, SHOW, EXPLAIN, DESCRIBE等）
                        columns = list(result.keys())
                        rows = result.fetchall()
                        return SQLResult(
                            success=True,
                            message="查询执行成功",
                            columns=columns,
                            rows=rows
                        )
                    else:
                        # 非查询语句（INSERT, UPDATE, DELETE等）
                        conn.commit()
                        return SQLResult(
                            success=True,
                            message="执行成功",
                            affected_rows=result.rowcount
                        )
                except Exception as e:
                    # 如果是非查询语句且执行失败，回滚事务
                    if not is_query_type:
                        conn.rollback()
                    raise
                        
        except MySQLError as e:
            logger.error(f"SQL执行错误: {e}, SQL: {statement}")
            return SQLResult(
                success=False,
                message=f"执行失败: {str(e)}"
            )
        except Exception as e:
            logger.error(f"未知错误: {e}, SQL: {statement}")
            return SQLResult(
                success=False,
                message=f"执行失败: {str(e)}"
            )

    def execute_multiple_statements(self, query: str) -> List[SQLResult]:
        """执行多条SQL语句
        
        Args:
            query: 包含多条SQL语句的查询字符串，以分号分隔
            
        Returns:
            SQL执行结果列表
        """
        statements = [stmt.strip() for stmt in query.split(';') if stmt.strip()]
        results = []
        
        for statement in statements:
            try:
                result = self.execute_single_statement(statement)
                results.append(result)
            except Exception as e:
                logger.warning(f"SQL执行警告: {e}, SQL: {statement}")
                results.append(SQLResult(
                    success=False,
                    message=f"执行失败: {str(e)}"
                ))
                
        return results

    def get_connection_pool_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息
        
        Returns:
            连接池统计信息
        """
        return self._connection_pool.get_stats()

    def _get_allowed_operations(self) -> Set[SQLOperation]:
        """获取当前角色允许的操作列表

        Returns:
            Set[SQLOperation]: 允许的操作集合
        """
        config = get_db_config()
        role = config.get("role", "readonly")  # 默认为只读角色
        return {SQLOperation.from_str(op) for op in get_role_permissions(role)}

    def clean_sql(self, sql: str) -> str:
        """清理SQL语句，移除注释和多余空白

        Args:
            sql: 原始SQL语句

        Returns:
            清理后的SQL语句
        """
        # 移除注释
        sql = self.SQL_COMMENT_PATTERN.sub('', sql)
        # 规范化空白字符
        return ' '.join(sql.split())

    def extract_operations(self, sql: str) -> Set[SQLOperation]:
        """提取SQL语句中的所有操作类型

        Args:
            sql: SQL语句

        Returns:
            操作类型集合
        """
        sql = self.clean_sql(sql.upper())
        return {
            op for op in SQLOperation
            if re.search(rf'\b{op.value}\b', sql)
        }

    def check_permissions(self, operations: Set[SQLOperation]) -> bool:
        """检查操作权限

        Args:
            operations: 操作类型集合

        Returns:
            是否有权限执行所有操作

        Raises:
            SQLPermissionError: 当权限不足时
        """
        allowed = self._get_allowed_operations()
        unauthorized = operations - allowed

        if unauthorized:
            raise SQLPermissionError(
                f"权限不足: 当前角色无权执行以下操作: {', '.join(op.value for op in unauthorized)}"
            )
        return True

    def format_result(self, result: SQLResult) -> str:
        """格式化SQL执行结果

        Args:
            result: SQL执行结果

        Returns:
            格式化后的结果字符串
        """
        if not result.success:
            return result.message

        if result.columns and result.rows:  # SELECT 类查询结果
            # 将所有值转换为字符串，None转换为"NULL"
            formatted_rows = [
                ",".join("NULL" if v is None else str(v) for v in row)
                for row in result.rows
            ]
            return "\n".join([",".join(result.columns)] + formatted_rows)
        else:  # 非查询语句结果
            return f"{result.message}。影响行数: {result.affected_rows}"