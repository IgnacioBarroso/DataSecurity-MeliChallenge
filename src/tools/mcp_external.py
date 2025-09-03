from src.config import settings
try:
    from mcpadapt import MCPClient  # type: ignore
except Exception:
    MCPClient = None  # type: ignore


def get_external_tools():
    """Obtiene herramientas del MCP externo; si no está disponible retorna []."""
    try:
        if MCPClient is None:
            return []
        mcp_url = f"{settings.MCP_EXTERNAL_PROTOCOL}://{settings.MCP_EXTERNAL_HOST}:{settings.MCP_EXTERNAL_PORT}"
        client = MCPClient(http_url=mcp_url)
        return client.get_tools() or []
    except Exception:
        return []

__all__ = ["get_external_tools"]
