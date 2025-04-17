from typing import Dict, Any, Sequence

from mcp import Tool
from mcp.types import TextContent

from .base import BaseHandler
from config import get_db_config
from handles import (
    ExecuteSQL
)

class GetTableIndex(BaseHandler):
    name = "get_table_index"
    description = (
        "根据表名搜索数据库中对应的表索引,支持多表查询(Search for table indexes in the database based on table names, supporting multi-table queries)"
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要搜索的表名"
                    }
                },
                "required": ["text"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """获取指定表的索引信息

        参数:
            text (str): 要查询的表名，多个表名以逗号分隔

        返回:
            list[TextContent]: 包含查询结果的TextContent列表
            - 返回表的索引名、索引字段、索引类型等信息
            - 结果按表名、索引名和索引顺序排序
            - 结果以CSV格式返回，包含列名和数据
        """
        try:
            if "text" not in arguments:
                raise ValueError("缺少查询语句")

            text = arguments["text"]

            config = get_db_config()
            execute_sql = ExecuteSQL()

            # 将输入的表名按逗号分割成列表
            table_names = [name.strip() for name in text.split(',')]
            # 构建IN条件
            table_condition = "','".join(table_names)

            sql = "SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME, SEQ_IN_INDEX, NON_UNIQUE, INDEX_TYPE "
            sql += f"FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = '{config['database']}' "
            sql += f"AND TABLE_NAME IN ('{table_condition}') ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;"

            return await execute_sql.run_tool({"query": sql})

        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]