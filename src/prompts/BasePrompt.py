from typing import ClassVar, Dict, Type, Any

from mcp import GetPromptResult
from mcp.types import Prompt

class PromptRegistry:
    """prompt注册表，用于管理所有prompt实例"""
    _prompts: ClassVar[Dict[str, 'BasePrompt']] = {}

    @classmethod
    def register(cls, prompt_class: Type['BasePrompt']) -> Type['BasePrompt']:
        """注册prompt类

        Args:
            prompt_class: 要注册的工具类

        Returns:
            返回注册的prompt类，方便作为装饰器使用
        """
        prompt = prompt_class()
        cls._prompts[prompt.name] = prompt
        return prompt_class

    @classmethod
    def get_prompt(cls, name: str) -> 'BasePrompt':
        """获取prompt实例

        Args:
            name: prompt名称

        Returns:
            prompt实例

        Raises:
            ValueError: 当prompt不存在时抛出
        """
        if name not in cls._prompts:
            raise ValueError(f"未知的prompt: {name}")
        return cls._prompts[name]

    @classmethod
    def get_all__prompts(cls) -> list[Prompt]:
        """获取所有prompt的描述

        Returns:
            所有prompt的描述列表
        """
        return [prompt.get_prompt() for prompt in cls._prompts.values()]


class BasePrompt:
    name:str = ""
    description:str = ""

    def __init_subclass__(cls, **kwargs):
        """子类初始化时自动注册到prompt注册表"""
        super().__init_subclass__(**kwargs)
        if cls.name:  # 只注册有名称的prompt
            PromptRegistry.register(cls)

    def get_prompt(self) -> Prompt:
        raise NotImplementedError()

    async def run_prompt(self, arguments: Dict[str, Any]) -> GetPromptResult:
        raise NotImplementedError()
