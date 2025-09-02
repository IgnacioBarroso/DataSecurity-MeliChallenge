"""
Servicio para orquestar y ejecutar los crews de análisis de seguridad bajo el patrón MCP.
"""
from src.mcp_crews import run_mcp_analysis
from src.models import SecurityReportInput # Importar desde src.models
from src.logging_config import setup_agent_trace_logging
import asyncio
import uuid

async def run_analysis_crew(report_input: SecurityReportInput) -> str:
    """
    Ejecuta el análisis de seguridad utilizando la arquitectura MCP requerida por el challenge.
    
    Esta función invoca el orquestador secuencial de `mcp_crews.py` en un hilo separado
    para no bloquear el event loop de FastAPI.
    """
    session_id = str(uuid.uuid4())
    agent_trace_logger = setup_agent_trace_logging(session_id)

    try:
        result = await asyncio.to_thread(run_mcp_analysis, report_input.text, agent_trace_logger)

        if not isinstance(result, str):
            if hasattr(result, 'raw') and result.raw:
                return result.raw
            if hasattr(result, 'json'):
                return result.json()
            return str(result)
        
        return result

    except Exception as e:
        agent_trace_logger.error(f"Error crítico durante la ejecución de la crew MCP para sesión {session_id}: {e}", exc_info=True)
        raise
