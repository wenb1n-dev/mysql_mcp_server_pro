import asyncio
import uvicorn

from typing import Sequence, Dict, Any
from mcp.server.sse import SseServerTransport

from mcp.server import Server
from mcp.types import Tool, TextContent, Prompt, GetPromptResult

from starlette.applications import Starlette
from starlette.routing import Route, Mount


from .handles.base import ToolRegistry
from .prompts.BasePrompt import PromptRegistry

# 初始化服务器
app = Server("operateMysql")

@app.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    """获取所有可用的提示模板列表
    
    返回:
        list[Prompt]: 返回系统中注册的所有提示模板列表
    """
    return PromptRegistry.get_all__prompts()


@app.get_prompt()
async def handle_get_prompt(name: str, arguments: Dict[str, Any] | None) -> GetPromptResult:
    """获取并执行指定的提示模板
    
    参数:
        name (str): 提示模板的名称
        arguments (dict[str, str] | None): 提示模板所需的参数字典，可以为空
        
    返回:
        GetPromptResult: 提示模板执行的结果
        
    说明:
        1. 根据提供的模板名称从注册表中获取对应的提示模板
        2. 使用提供的参数执行该模板
        3. 返回执行结果
    """
    prompt = PromptRegistry.get_prompt(name)
    return await prompt.run_prompt(arguments)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
        列出所有可用的MySQL操作工具
    """
    return ToolRegistry.get_all_tools()

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """调用指定的工具执行操作
    
    Args:
        name (str): 工具名称
        arguments (dict): 工具参数

    Returns:
        Sequence[TextContent]: 工具执行结果

    Raises:
        ValueError: 当指定了未知的工具名称时抛出异常
    """
    tool = ToolRegistry.get_tool(name)

    return await tool.run_tool(arguments)


async def run_stdio():
    """运行标准输入输出模式的服务器
    
    使用标准输入输出流(stdio)运行服务器，主要用于命令行交互模式
    
    Raises:
        Exception: 当服务器运行出错时抛出异常
    """
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        try:
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
        except Exception as e:
            print(f"服务器错误: {str(e)}")
            raise

def run_sse():
    """运行SSE(Server-Sent Events)模式的服务器
    
    启动一个支持SSE的Web服务器，允许客户端通过HTTP长连接接收服务器推送的消息
    服务器默认监听0.0.0.0:9000
    """
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        """处理SSE连接请求
        
        Args:
            request: HTTP请求对象
        """
        async with sse.connect_sse(
                request.scope, request.receive, request._send
        ) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message)
        ],
    )
    uvicorn.run(starlette_app, host="0.0.0.0", port=9000)



def main(mode="sse"):
    """
    主入口函数，用于命令行启动
    支持两种模式：
    1. SSE 模式（默认）：mysql-mcp-server
    2. stdio 模式：mysql-mcp-server --stdio
    
    Args:
        mode (str): 运行模式，可选值为 "sse" 或 "stdio"
    """
    import sys
    
    # 命令行参数优先级高于默认参数
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        # 标准输入输出模式
        asyncio.run(run_stdio())
    elif len(sys.argv) > 1 and sys.argv[1] == "--sse":
        # SSE 模式
        run_sse()
    else:
        # 使用传入的默认模式
        if mode == "stdio":
            asyncio.run(run_stdio())
        else:
            run_sse()

if __name__ == "__main__":
    main()
