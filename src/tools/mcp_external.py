from mcpadapt import MCPClient
from src.config import settings


def get_external_tools():
    """
    Inicializa perezosamente el cliente MCP externo y devuelve la lista de herramientas.
    Si el servidor MCP no está disponible, retorna una lista vacía.
    """
    try:
        mcp_url = f"{settings.MCP_EXTERNAL_PROTOCOL}://{settings.MCP_EXTERNAL_HOST}:{settings.MCP_EXTERNAL_PORT}"
        client = MCPClient(http_url=mcp_url)
        return client.get_tools() or []
    except Exception:
        return []

__all__ = ["get_external_tools"]
