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
    Ejecuta la SecurityAnalysisCrew y retorna el reporte final en JSON y session_id.
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
    import json
    # Loggear el resultado crudo para depuración
    print("\n[DEBUG] Raw pipeline result:")
    print(json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, dict) else str(result))
    # Validate expected fields for FinalReport
    expected_fields = ["application_name", "summary", "prioritized_detectors"]
    if isinstance(result, dict):
        missing = [f for f in expected_fields if f not in result or not result.get(f)]
        if missing:
            print(f"[WARNING] FinalReport is missing fields: {missing}")
        return {"report_json": json.dumps(result, ensure_ascii=False, indent=2), "session_id": session_id, "missing_fields": missing}
    # Si no es un dict, retornar advertencia
    return {"report_json": "{}", "session_id": session_id, "missing_fields": expected_fields}

# Exponer para tests
__all__ = ["run_analysis_crew", "run_mcp_analysis", "setup_agent_trace_logging"]
