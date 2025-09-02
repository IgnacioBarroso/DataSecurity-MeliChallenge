from crewai.tools import tool
from src.tools.retriever import query_dbir_report

@tool("DBIR Report RAG Tool")
def dbir_rag_tool(query: str) -> str:
    """Úsala para hacer preguntas específicas al informe DBIR 2025 de Verizon. "
    "Esta herramienta es tu única fuente de conocimiento sobre tendencias de amenazas, "
    "vectores de ataque, estadísticas de brechas y patrones de incidentes. "
    "Formula preguntas claras y concisas para obtener la información más relevante."""
    return query_dbir_report(query)