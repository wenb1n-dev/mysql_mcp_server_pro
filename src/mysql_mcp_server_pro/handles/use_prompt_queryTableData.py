from typing import Dict, Sequence, Any

from mcp import Tool
from mcp.types import TextContent

from .base import BaseHandler

"""

#背景
    - 该工具仅做研究探索使用
    - 主要探索mcp是否能够形成一条链式，根据内置定义的prompt自动调用所需的所有工具，使得模型更精准的调用。

#效果
    - 模型确实能够形成链式进行调用
    - 具有局限性，即只能针对某种情况进行定义，固定的要求它调用指定的工具
    
#使用方式
    - 该工具不作为常用的固定工具，如同样想要尝试链式的，可以将该工具继承BaseHandler类，
    即将下面的class UsePromptQueryTableData() 改为 class UsePromptQueryTableData(BaseHandler) 
    
# Background
    - This tool is for research and exploration purposes only.
    - The main goal is to explore whether MCP can form a chain, automatically invoking all required tools based on built-in prompt definitions, 
    enabling the model to call tools more accurately.

# Effect
    - The model can indeed perform chained invocations.
    - There are limitations: it can only be defined for certain scenarios, requiring fixed rules to call specified tools.

# Usage
    - This tool is not intended as a regular fixed tool. If you also want to experiment with chaining, you can inherit this tool from the BaseHandler class,
    i.e., change the following class UsePromptQueryTableData() to class UsePromptQueryTableData(BaseHandler)
"""

class UsePromptQueryTableData():
    name = "use_prompt_queryTableData"
    description = (
        "查询表中的数据信息的提示词，根据需求在调用对应工具返回结果，（Retrieve data records from the database table.）"
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
        prompt = f"""
                - Workflow:
                  1. 解析用户输入的自然语言指令，提取关键信息，如表描述和查询条件。
                  2. 判断是否跨库查询、是否明确指定了目标表名（例如是中文的描述、英文的描述，偏向语义化的描述则判断为未明确表名）
                  3. 未明确指定目标表名则调用“get_table_name”工具，获取对应的表名。
                  4. 调用“get_table_desc”工具，获取表的结构信息。
                  5. 根据表结构信息和用户输入的查询条件，生成SQL查询语句并调用“execute_sql”工具，返回查询结果。
                - Examples:
                  - 例子1：用户输入“查询用户表张三的数据”
                    解析结果：表描述为“用户表”，查询条件为“张三”。
                    判断结果：1.没有出现跨库的情况 2.未明确指定表名，当前为表的描述，需调用工具获取表名
                    调用工具“get_table_name”：根据“用户表”描述获取表名，假设返回表名为“user_table”。
                    调用工具“get_table_desc”：根据“user_table”获取表结构，假设表结构包含字段“id”、“name”、“age”。
                    生成SQL查询语句：`SELECT * FROM user_table WHERE name = '张三';`
                    调用工具“execute_sql”：根据生成的SQL,获取结果。
                    查询结果：返回张三的相关数据。
                - task: 
                  - 调用工具“get_table_name”，
                  - 调用工具“get_table_desc”，
                  - 调用工具“execute_sql”
                  - 以markdown格式返回执行结果
                """

        return [TextContent(type="text", text=prompt)]