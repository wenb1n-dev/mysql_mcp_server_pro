from mysql_mcp_server_pro.server import main

def stdio_entry():
    """stdio 模式入口点"""
    main(mode="stdio")

def sse_entry():
    """SSE 模式入口点"""
    main(mode="sse")

def streamable_http_entry():
    """Streamable Http 入口点"""
    main(mode="streamable_http")