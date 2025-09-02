"""
Servicio para ejecutar la SecurityAnalysisCrew (MCP de 3 agentes).
"""

import uuid
import asyncio

from src.mcp_crews import SecurityAnalysisCrew, run_mcp_analysis
from src.logging_config import setup_session_logging as setup_agent_trace_logging


from src.models import SecurityReportInput

async def run_analysis_crew(user_input: str | SecurityReportInput):
    """
    Ejecuta la SecurityAnalysisCrew y retorna el reporte markdown y session_id.
    Usa internamente run_mcp_analysis y setup_agent_trace_logging para permitir mocking en tests.
    """
    session_id = str(uuid.uuid4())
    logger = setup_agent_trace_logging(session_id)
    # Si el input es un modelo Pydantic, extraer el texto
    if isinstance(user_input, SecurityReportInput):
        user_input_str = user_input.text
    else:
        user_input_str = str(user_input)
    result = await asyncio.to_thread(run_mcp_analysis, user_input_str, logger)
    # Si el resultado es un string JSON (como espera el test), devuélvelo tal cual
    if isinstance(result, str) and result.strip().startswith("{"):
        return result
    return {"report": result, "session_id": session_id}

# Exponer para tests
__all__ = ["run_analysis_crew", "run_mcp_analysis", "setup_agent_trace_logging"]
