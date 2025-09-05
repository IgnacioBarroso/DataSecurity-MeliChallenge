"""
Servicio para ejecutar la SecurityAnalysisCrew (MCP de 3 agentes).
"""

import uuid
import asyncio
import json
import time

from src.mcp_crews import SecurityAnalysisCrew, run_mcp_analysis
from src.logging_config import setup_session_logging as setup_agent_trace_logging
from src.config import settings
from src.turbo_pipeline import run_turbo_pipeline, _normalize_report as _normalize_turbo_report


def _normalize_heavy_report(data: dict) -> dict:
    """Normalize heavy-mode report minimally: dedupe actionable_steps and map severity to H/M/L.
    Does NOT change the number of detectors to avoid altering heavy semantics.
    """
    try:
        plist = data.get("prioritized_detectors")
        if not isinstance(plist, list):
            return data
        try:
            from rapidfuzz import fuzz  # type: ignore
            have_fuzz = True
        except Exception:
            have_fuzz = False
        out = []
        for det in plist:
            if not isinstance(det, dict):
                continue
            steps = det.get("actionable_steps") or []
            if not isinstance(steps, list):
                steps = [str(steps)] if steps else []
            normalized_steps = []
            if have_fuzz:
                for s in [str(s).strip() for s in steps if str(s).strip()]:
                    if not normalized_steps:
                        normalized_steps.append(s)
                        continue
                    from rapidfuzz import fuzz as _f
                    if max((_f.ratio(s.lower(), t.lower()) for t in normalized_steps), default=0) < 90:
                        normalized_steps.append(s)
            else:
                seen = set()
                for s in [str(s).strip().lower() for s in steps if str(s).strip()]:
                    if s not in seen:
                        seen.add(s); normalized_steps.append(s)
            sev = (det.get("severity") or "Medium").title()
            if sev not in ("High", "Medium", "Low"):
                sev = "High" if sev.lower() == "critical" else "Medium"
            new_det = det.copy()
            new_det["actionable_steps"] = normalized_steps
            new_det["severity"] = sev
            out.append(new_det)
        data["prioritized_detectors"] = out
    except Exception:
        return data
    return data


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
    t0 = time.perf_counter()
    if settings.is_turbo:
        # Pipeline rápido sin CrewAI
        result = await asyncio.to_thread(run_turbo_pipeline, user_input_str)
    else:
        result = await asyncio.to_thread(run_mcp_analysis, user_input_str, logger)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
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
        # Limpieza de artefactos turbo legado y normalización en modo turbo
        if settings.is_turbo:
            try:
                if "report_json" in target and isinstance(target["report_json"], str):
                    target = json.loads(target["report_json"])  # unwrap legacy nested
            except Exception:
                pass
            # Remover banderas auxiliares
            if isinstance(target, dict):
                target.pop("cached", None)
                target.pop("session_id", None)
                # Normalizar severidades y asegurar 5 detectores
                target = _normalize_turbo_report(target)
        else:
            # Heavy: dedupe steps y normalizar severidades sin cambiar la longitud
            target = _normalize_heavy_report(target)
        missing = [f for f in expected_fields if f not in target or not target.get(f)]
        if missing:
            print(f"[WARNING] FinalReport is missing fields: {missing}")
        return {"report_json": json.dumps(target, ensure_ascii=False, indent=2), "session_id": session_id, "missing_fields": missing, "timing_ms": elapsed_ms}
    
    # Si no es un dict, retornar advertencia
    return {"report_json": "{}", "session_id": session_id, "missing_fields": expected_fields, "timing_ms": elapsed_ms}

# Exponer para tests
__all__ = ["run_analysis_crew", "run_mcp_analysis", "setup_agent_trace_logging"]
