from typing import Dict, Any, Sequence
import logging

from mcp import Tool
from mcp.types import TextContent

from .base import BaseHandler
from mysql_mcp_server_pro.exception.exceptions import SQLExecutionError
from ..utils.execute_sql_util import ExecuteSqlUtil


logger = logging.getLogger(__name__)

class ExecuteSQL(BaseHandler):
    """SQL 执行处理器"""
    
    name = "execute_sql"
    description = "在MySQL数据库上执行SQL (支持多条SQL语句，以分号分隔)"

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
        
        try:
            exe = ExecuteSqlUtil()
            sql_results = exe.execute_multiple_statements(query)
            
            # 格式化结果
            results = []
            for result in sql_results:
                formatted_result = exe.format_result(result)
                results.append(formatted_result)
            
            return [TextContent(type="text", text="\n---\n".join(results))]
            
        except SQLExecutionError as e:
            return [TextContent(type="text", text=str(e))]