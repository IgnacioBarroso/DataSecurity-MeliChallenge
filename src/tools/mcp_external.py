from src.config import settings


def get_external_tools():
    """
    Inicializa perezosamente el cliente MCP externo y devuelve la lista de herramientas.
    Si el servidor MCP no está disponible, retorna una lista vacía.
    """
    try:
        # Importación perezosa para evitar fallos si cambia la API o no está instalado
        from mcpadapt import MCPClient  # type: ignore
        mcp_url = f"{settings.MCP_EXTERNAL_PROTOCOL}://{settings.MCP_EXTERNAL_HOST}:{settings.MCP_EXTERNAL_PORT}"
        client = MCPClient(http_url=mcp_url)
        return client.get_tools() or []
    except Exception:
        # Si MCP no está disponible o API cambió, continuar sin herramientas externas
        return []

__all__ = ["get_external_tools"]
