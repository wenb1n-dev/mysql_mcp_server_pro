from typing import Dict, Sequence, Any

from mcp import Tool
from mcp.types import TextContent

from .base import BaseHandler
from config import get_db_config
from handles import (
    ExecuteSQL
)


class GetTableDesc(BaseHandler):
    name = "get_table_desc"
    description = (
        "根据表名搜索数据库中对应的表字段,支持多表查询(Search for table structures in the database based on table names, supporting multi-table queries)"
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
            """获取指定表的字段结构信息

            参数:
                text (str): 要查询的表名，多个表名以逗号分隔

            返回:
                list[TextContent]: 包含查询结果的TextContent列表
                - 返回表的字段名、字段注释等信息
                - 结果按表名和字段顺序排序
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
                sql = "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_COMMENT "
                sql += f"FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '{config['database']}' "
                sql += f"AND TABLE_NAME IN ('{table_condition}') ORDER BY TABLE_NAME, ORDINAL_POSITION;"
                return await execute_sql.run_tool({"query":sql})

            except Exception as e:
                return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]