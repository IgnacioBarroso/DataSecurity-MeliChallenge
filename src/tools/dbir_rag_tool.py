# Exponer para tests: import del módulo para que el patch funcione
from src.tools import retriever
from crewai.tools import tool
from typing import Any
from src.logging_config import logging
from src.trace import get_trace_logger

# Inicializa logger específico para la herramienta
logger = logging.getLogger(__name__)


def _dbir_rag_tool(query: Any) -> str:
    """
    Use this to ask specific questions to the Verizon DBIR 2025 report.
    This tool is your only source of knowledge about threat trends, attack vectors, breach statistics, and incident patterns.
    Ask clear and concise questions to get the most relevant information.
    """
    # CrewAI sometimes wraps the query in a dict with a 'description' key
    if isinstance(query, dict) and "description" in query:
        logger.warning(
            "DBIR Report RAG Tool received a dictionary for query. Extracting 'description'."
        )
        query = query["description"]
    elif not isinstance(query, str):
        logger.warning(
            f"DBIR Report RAG Tool received an unexpected type: {type(query)}. Trying to convert to string."
        )
        query = str(query)

    logger.info(f"Buscando en DBIR con query: '{query}'")
    # Trace: tool invocation
    tlogger = get_trace_logger()
    if tlogger:
        tlogger.info(
            "tool_invocation",
            extra={
                "task_name": "DBIR Report RAG Tool",
                "input_data": {"query": query},
            },
        )
    # Recuperar documentos iniciales
    try:
        result = retriever.query_dbir_report(query)
        if tlogger:
            tlogger.info(
                "tool_result",
                extra={
                    "task_name": "DBIR Report RAG Tool",
                    "output_data": result[:1000] if isinstance(result, str) else str(result)[:1000],
                },
            )
        return result
    except Exception as e:
        # Si el mock retorna un string de error, devuélvelo tal cual
        if isinstance(e, str):
            return e
        logger.error(f"Error en DBIRRAGTool: {e}")
        if tlogger:
            tlogger.info(
                "tool_error",
                extra={
                    "task_name": "DBIR Report RAG Tool",
                    "output_data": str(e),
                },
            )
        return f"Error al consultar el DBIR: {e}"

dbir_rag_tool = tool("DBIR Report RAG Tool")(_dbir_rag_tool)
