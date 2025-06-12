from typing import Dict, Any, Sequence

from mcp import Tool
from mcp.types import TextContent

from .base import BaseHandler
from mysql_mcp_server_pro.config import get_db_config
from mysql_mcp_server_pro.handles import (
    ExecuteSQL
)

execute_sql = ExecuteSQL()

class GetDBHealthIndexUsage(BaseHandler):
    name = "get_db_health_index_usage"
    description = (
        "获取当前连接的mysql库的索引使用情况,包含冗余索引情况、性能较差的索引情况、未使用索引且查询时间大于30秒top5情况"
        + "(Get the index usage of the currently connected mysql database, including redundant index situations, "
        +  "poorly performing index situations, and the top 5 unused index situations with query times greater than 30 seconds)"
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
        config = get_db_config()

        count_zero_result = await self.get_count_zero(arguments,config)
        max_time_result = await self.get_max_timer(arguments,config)
        not_used_index_result = await self.get_not_used_index(arguments,config)


        # 合并结果
        combined_result = []
        combined_result.extend(count_zero_result)
        combined_result.extend(max_time_result)
        combined_result.extend(not_used_index_result)


        return combined_result

    """
        获取冗余索引情况
    """
    async def get_count_zero(self, arguments: Dict[str, Any], config) -> Sequence[TextContent]:
        try:
            sql = "SELECT object_name,index_name,count_star from performance_schema.table_io_waits_summary_by_index_usage "
            sql += f"WHERE object_schema = '{config['database']}' and count_star = 0 AND sum_timer_wait = 0 ;"

            return await execute_sql.run_tool({"query": sql})
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]


    """
        获取性能较差的索引情况
    """
    async def get_max_timer(self, arguments: Dict[str, Any], config) -> Sequence[TextContent]:
        try:
            sql = "SELECT object_schema,object_name,index_name,(max_timer_wait / 1000000000000) max_timer_wait "
            sql += f"FROM performance_schema.table_io_waits_summary_by_index_usage where object_schema = '{config['database']}' "
            sql += "and index_name is not null ORDER BY  max_timer_wait DESC;"

            return await execute_sql.run_tool({"query": sql})
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]

    """
        获取未使用索引查询时间大于30秒的top5情况
    """
    async def get_not_used_index(self, arguments: Dict[str, Any], config) -> Sequence[TextContent]:
        try:
            sql = "SELECT object_schema,object_name, (max_timer_wait / 1000000000000) max_timer_wait "
            sql += f"FROM performance_schema.table_io_waits_summary_by_index_usage where object_schema = '{config['database']}' "
            sql += "and index_name IS null and max_timer_wait > 30000000000000 ORDER BY max_timer_wait DESC limit 5;"

            return await execute_sql.run_tool({"query": sql})
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]