from typing import Dict, Any, Sequence, Type, ClassVar

from mcp.types import TextContent, Tool


class ToolRegistry:
    """工具注册表，用于管理所有工具实例"""
    _tools: ClassVar[Dict[str, 'BaseHandler']] = {}

    @classmethod
    def register(cls, tool_class: Type['BaseHandler']) -> Type['BaseHandler']:
        """注册工具类
        
        Args:
            tool_class: 要注册的工具类
            
        Returns:
            返回注册的工具类，方便作为装饰器使用
        """
        tool = tool_class()
        cls._tools[tool.name] = tool
        return tool_class

    @classmethod
    def get_tool(cls, name: str) -> 'BaseHandler':
        """获取工具实例
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例
            
        Raises:
            ValueError: 当工具不存在时抛出
        """
        if name not in cls._tools:
            raise ValueError(f"未知的工具: {name}")
        return cls._tools[name]

    @classmethod
    def get_all_tools(cls) -> list[Tool]:
        """获取所有工具的描述
        
        Returns:
            所有工具的描述列表
        """
        return [tool.get_tool_description() for tool in cls._tools.values()]


class BaseHandler:
    """工具基类"""
    name: str = ""
    description: str = ""

    def __init_subclass__(cls, **kwargs):
        """子类初始化时自动注册到工具注册表"""
        super().__init_subclass__(**kwargs)
        if cls.name:  # 只注册有名称的工具
            ToolRegistry.register(cls)

    def get_tool_description(self) -> Tool:
        raise NotImplementedError

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        raise NotImplementedError

