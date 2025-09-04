"""
Servicio para ejecutar la SecurityAnalysisCrew (MCP de 3 agentes).
"""

import uuid
import asyncio
import json

from src.mcp_crews import SecurityAnalysisCrew, run_mcp_analysis
from src.logging_config import setup_session_logging as setup_agent_trace_logging
from src.config import settings
from src.turbo_pipeline import run_turbo_pipeline


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
    if settings.is_turbo:
        # Pipeline rápido sin CrewAI
        result = await asyncio.to_thread(run_turbo_pipeline, user_input_str)
    else:
        result = await asyncio.to_thread(run_mcp_analysis, user_input_str, logger)
    # Normalizar a dict si vino como string/TaskOutput serializado
    normalized: dict | None = None
    if isinstance(result, dict):
        normalized = result
    elif isinstance(result, str):
        try:
            obj = json.loads(result)
            if isinstance(obj, dict):
                raw = obj.get("raw")
                if isinstance(raw, str):
                    try:
                        data = json.loads(raw)
                        if isinstance(data, dict):
                            normalized = data
                    except Exception:
                        normalized = obj
                else:
                    normalized = obj
        except Exception:
            normalized = None
            
    # Loggear el resultado crudo para depuración
    print("\n[DEBUG] Raw pipeline result:")
    print(json.dumps(normalized, ensure_ascii=False, indent=2) if isinstance(normalized, dict) else str(result))
    
    # Validate expected fields for FinalReport
    expected_fields = ["application_name", "summary", "prioritized_detectors"]
    target = normalized if normalized is not None else (result if isinstance(result, dict) else None)
    if isinstance(target, dict):
        missing = [f for f in expected_fields if f not in target or not target.get(f)]
        if missing:
            print(f"[WARNING] FinalReport is missing fields: {missing}")
        return {"report_json": json.dumps(target, ensure_ascii=False, indent=2), "session_id": session_id, "missing_fields": missing}
    
    # Si no es un dict, retornar advertencia
    return {"report_json": "{}", "session_id": session_id, "missing_fields": expected_fields}

# Exponer para tests
__all__ = ["run_analysis_crew", "run_mcp_analysis", "setup_agent_trace_logging"]
