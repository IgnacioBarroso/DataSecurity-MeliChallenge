from src.config import settings
try:
    from mcpadapt import MCPClient  # type: ignore
except Exception:
    MCPClient = None  # type: ignore

_CACHED_MCP_CLIENT = None
_CACHED_MCP_TOOLS = None


def get_external_tools():
    """Obtiene herramientas del MCP externo (cacheadas). Si no está disponible retorna []."""
    global _CACHED_MCP_CLIENT, _CACHED_MCP_TOOLS
    try:
        if MCPClient is None:
            return []
        if _CACHED_MCP_TOOLS is not None:
            return _CACHED_MCP_TOOLS
        mcp_url = f"{settings.MCP_EXTERNAL_PROTOCOL}://{settings.MCP_EXTERNAL_HOST}:{settings.MCP_EXTERNAL_PORT}"
        _CACHED_MCP_CLIENT = MCPClient(http_url=mcp_url, timeout=5)
        _CACHED_MCP_TOOLS = _CACHED_MCP_CLIENT.get_tools() or []
        return _CACHED_MCP_TOOLS
    except Exception:
        return []

__all__ = ["get_external_tools"]
