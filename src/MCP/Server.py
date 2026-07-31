from mcp.server import MCPServer


def create_server(name: str = "Gmail-MCP") -> MCPServer:
    return MCPServer(name)
