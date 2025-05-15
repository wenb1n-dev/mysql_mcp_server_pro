from typing import Dict, Any, Sequence

from mcp import Tool
from mcp.types import TextContent
from pypinyin import pinyin, Style
from .base import BaseHandler


class GetChineseInitials(BaseHandler):
    name = "get_chinese_initials"
    description = (
        "创建表结构时，将中文字段名转换为拼音首字母字段"
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
                        "description": "要获取拼音首字母的汉字文本，以“,”分隔"
                    }
                },
                "required": ["text"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
            """将中文文本转换为拼音首字母

            参数:
                text (str): 要转换的中文文本，以中文逗号分隔

            返回:
                list[TextContent]: 包含转换结果的TextContent列表
                - 每个词的首字母会被转换为大写
                - 多个词的结果以英文逗号连接

            示例:
                get_chinese_initials("用户名，密码")
                [TextContent(type="text", text="YHM,MM")]
            """
            try:
                if "text" not in arguments:
                    raise ValueError("缺少查询语句")

                text = arguments["text"]

                # 将文本按逗号分割
                words = text.split('，')

                # 存储每个词的首字母
                initials = []

                for word in words:
                    # 获取每个字的拼音首字母
                    word_pinyin = pinyin(word, style=Style.FIRST_LETTER)
                    # 将每个字的首字母连接起来
                    word_initials = ''.join([p[0].upper() for p in word_pinyin])
                    initials.append(word_initials)

                # 用逗号连接所有结果
                return [TextContent(type="text", text=','.join(initials))]

            except Exception as e:
                return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]