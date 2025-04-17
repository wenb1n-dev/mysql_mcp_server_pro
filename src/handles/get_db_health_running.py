from typing import Dict, Any, Sequence

from mcp import Tool
from mcp.types import TextContent

from .base import BaseHandler

from handles import (
    ExecuteSQL
)

execute_sql = ExecuteSQL()

class GetDBHealthRunning(BaseHandler):
    name = "get_db_health_running"
    description = (
        "获取当前mysql的健康状态(Analyze MySQL health status )"
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {

                }
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        lock_result = await self.get_lock(arguments)
        processlist_result = await self.get_processlist(arguments)
        status_result = await self.get_status(arguments)
        trx_result = await self.get_trx(arguments)


        # 合并结果
        combined_result = []
        combined_result.extend(processlist_result)
        combined_result.extend(lock_result)
        combined_result.extend(trx_result)
        combined_result.extend(status_result)

        return combined_result

    """
        获取连接情况
    """
    async def get_processlist(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        try:
            sql = "SHOW FULL PROCESSLIST;SHOW VARIABLES LIKE 'max_connections';"

            return await execute_sql.run_tool({"query": sql})
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]

    """
        获取运行情况
    """
    async def get_status(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        try:
            sql = "SHOW ENGINE INNODB STATUS;"

            return await execute_sql.run_tool({"query": sql})
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]

    """
        获取事务情况
    """
    async def get_trx(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        try:
            sql = "SELECT * FROM INFORMATION_SCHEMA.INNODB_TRX;"
            return await execute_sql.run_tool({"query": sql})
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]


    """
        获取锁情况
    """
    async def get_lock(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        try:
            sql = "SHOW OPEN TABLES WHERE In_use > 0;select * from information_schema.innodb_locks;select * from information_schema.innodb_lock_waits;"

            return await execute_sql.run_tool({"query": sql})
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]