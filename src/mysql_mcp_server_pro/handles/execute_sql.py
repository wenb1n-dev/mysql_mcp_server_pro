from typing import Dict, Any, Sequence, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import logging
from contextlib import contextmanager

from mysql.connector import connect, Error as MySQLError
from mysql.connector.cursor import MySQLCursor
from mysql.connector.connection import MySQLConnection
from mcp import Tool
from mcp.types import TextContent

from .base import BaseHandler
from ..config import get_db_config, get_role_permissions
from ..handles.exceptions import SQLPermissionError, SQLExecutionError

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
    """SQL 执行结果"""
    success: bool
    message: str
    columns: Optional[List[str]] = None
    rows: Optional[List[Tuple]] = None
    affected_rows: int = 0

class ExecuteSQL(BaseHandler):
    """SQL 执行处理器"""
    
    name = "execute_sql"
    description = "在MySQL数据库上执行SQL (支持多条SQL语句，以分号分隔)"

    # SQL操作正则模式
    SQL_COMMENT_PATTERN = re.compile(r'--.*$|/\*.*?\*/', re.MULTILINE|re.DOTALL)
    
    def _get_allowed_operations(self) -> Set[SQLOperation]:
        """获取当前角色允许的操作列表
        
        Returns:
            Set[SQLOperation]: 允许的操作集合
        """
        config = get_db_config()
        role = config.get("role", "readonly")  # 默认为只读角色
        return {SQLOperation.from_str(op) for op in get_role_permissions(role)}

    def get_tool_description(self) -> Tool:
        """获取工具描述"""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要执行的SQL语句"
                    }
                },
                "required": ["query"]
            }
        )

    @staticmethod
    def clean_sql(sql: str) -> str:
        """清理SQL语句，移除注释和多余空白
        
        Args:
            sql: 原始SQL语句
            
        Returns:
            清理后的SQL语句
        """
        # 移除注释
        sql = ExecuteSQL.SQL_COMMENT_PATTERN.sub('', sql)
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

    @contextmanager
    def get_db_connection(self):
        """获取数据库连接的上下文管理器"""
        config = get_db_config()
        conn_params = {k: v for k, v in config.items() if k != "role"}
        
        try:
            connection = connect(**conn_params)
            yield connection
        except MySQLError as e:
            logger.error(f"数据库连接失败: {e}")
            raise SQLExecutionError(f"数据库连接失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()

    def execute_single_statement(
        self, 
        cursor: MySQLCursor, 
        statement: str,
        conn: MySQLConnection
    ) -> SQLResult:
        """执行单条SQL语句
        
        Args:
            cursor: 数据库游标
            statement: SQL语句
            conn: 数据库连接
            
        Returns:
            执行结果
            
        Raises:
            SQLPermissionError: 当权限不足时
            SQLExecutionError: 当执行出错时
        """
        try:
            # 检查权限
            operations = self.extract_operations(statement)
            self.check_permissions(operations)

            cursor.execute(statement)
            
            if cursor.description:  # SELECT 类查询
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return SQLResult(
                    success=True,
                    message="查询执行成功",
                    columns=columns,
                    rows=rows
                )
            else:  # 非查询语句
                conn.commit()
                return SQLResult(
                    success=True,
                    message="执行成功",
                    affected_rows=cursor.rowcount
                )
                
        except MySQLError as e:
            logger.error(f"SQL执行错误: {e}, SQL: {statement}")
            raise SQLExecutionError(f"执行失败: {e}")

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

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """执行SQL工具
        
        Args:
            arguments: 包含SQL查询的参数字典
            
        Returns:
            执行结果文本序列
        """
        if "query" not in arguments:
            return [TextContent(type="text", text="错误: 缺少查询语句")]

        query = arguments["query"]
        statements = [stmt.strip() for stmt in query.split(';') if stmt.strip()]
        results = []

        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    for statement in statements:
                        try:
                            result = self.execute_single_statement(cursor, statement, conn)
                            results.append(self.format_result(result))
                        except (SQLPermissionError, SQLExecutionError) as e:
                            results.append(str(e))
                            logger.warning(f"SQL执行警告: {e}, SQL: {statement}")
                            continue

            return [TextContent(type="text", text="\n---\n".join(results))]
            
        except SQLExecutionError as e:
            return [TextContent(type="text", text=str(e))]

