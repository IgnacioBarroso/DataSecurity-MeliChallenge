"""
Implementación de la arquitectura MCP (Model-Controller-Plane) para CrewAI.

Este módulo define el patrón de orquestación secuencial requerido por el challenge,
_donde el output de una sub-crew se convierte en el input de la siguiente.
"""

try:
    from pydantic import BaseModel  # type: ignore
except Exception:
    BaseModel = object  # fallback

import json
import logging
from crewai import Crew, Process, Task
from src.agents import reporting_agent, risk_classifier_agent, threat_analyzer_agent
from src.llm_provider import get_llm
from src.models import EnrichedFindings, FinalReport, ThreatFindings
from src.trace import set_trace_logger



llm = get_llm()


# --- Crew principal de 3 agentes MCP ---
class SecurityAnalysisCrew:
    def __init__(self, agent_trace_logger: logging.Logger, llm_instance=None):
        self.agent_trace_logger = agent_trace_logger
        self.llm = llm_instance or llm
        # Instanciar agentes, permitiendo inyección de llm si es necesario
        # Siempre pasamos llm_override, ya que ahora los agentes lo aceptan opcionalmente
        self.analyzer = threat_analyzer_agent(llm_override=self.llm)
        self.classifier = risk_classifier_agent(llm_override=self.llm)
        self.reporter = reporting_agent(llm_override=self.llm)

    def run(self, user_input: str):
        # 1. Task: Threat analysis
        analysis_task = Task(
            description=f"Analyze the user's input and find up to 5 relevant threats using DBIR: {user_input}",
            expected_output="List of threats (ThreatFinding) in JSON.",
            agent=self.analyzer,
            output_pydantic=ThreatFindings,
        )
        # 2. Task: Risk classification
        classification_task = Task(
            description="Enrich the findings with MITRE ATT&CK and classify the risk.",
            expected_output="List of enriched threats (EnrichedFinding) in JSON.",
            agent=self.classifier,
            context=[analysis_task],
            output_pydantic=EnrichedFindings,
        )
        # 3. Task: Final report generation
        reporting_task = Task(
            description="Generate the final report in valid JSON format (FinalReport schema) with prioritized and actionable detectors.",
            expected_output="Final report (FinalReport) in JSON.",
            agent=self.reporter,
            context=[classification_task],
            output_pydantic=FinalReport,
        )
        crew = Crew(
            agents=[self.analyzer, self.classifier, self.reporter],
            tasks=[analysis_task, classification_task, reporting_task],
            process=Process.sequential,
            verbose=True
        )
        # Establecer trace logger global y ejecutar
        set_trace_logger(self.agent_trace_logger)
        result = crew.kickoff()
        try:
            logger = self.agent_trace_logger or logging.getLogger("agent_trace")
            session_id = logger.name.replace("agent_trace_", "") if logger.name.startswith("agent_trace_") else None
            # Log de inputs/outputs de cada tarea (best-effort) usando JsonFormatter extras
            def _safe_preview(obj):
                try:
                    if isinstance(obj, BaseModel):
                        return obj.model_dump()  # serializable
                except Exception:
                    pass
                try:
                    return str(obj)[:2000]
                except Exception:
                    return None

            logger.info(
                "task_analysis_completed",
                extra={
                    "session_id": session_id,
                    "task_name": "analysis",
                    "input_data": user_input,
                    "output_data": _safe_preview(getattr(analysis_task, "output", None)),
                },
            )
            logger.info(
                "task_classification_completed",
                extra={
                    "session_id": session_id,
                    "task_name": "classification",
                    "input_data": _safe_preview(getattr(analysis_task, "output", None)),
                    "output_data": _safe_preview(getattr(classification_task, "output", None)),
                },
            )
            logger.info(
                "task_reporting_completed",
                extra={
                    "session_id": session_id,
                    "task_name": "reporting",
                    "input_data": _safe_preview(getattr(classification_task, "output", None)),
                    "output_data": _safe_preview(getattr(reporting_task, "output", None)),
                },
            )
        except Exception:
            # Si CrewAI no expone outputs, ignorar silenciosamente
            pass
        finally:
            # Limpiar trace logger global
            set_trace_logger(None)

        # Intentar retornar JSON estricto del resultado final
        try:
            if hasattr(reporting_task, "output") and isinstance(reporting_task.output, BaseModel):
                return reporting_task.output.model_dump_json()
        except Exception:
            pass
        # Si CrewAI retorna un TaskOutput con campo raw (JSON), extraerlo
        try:
            o = getattr(reporting_task, "output", None)
            raw = None
            if o is not None:
                raw = getattr(o, "raw", None)
                if raw is None and isinstance(o, dict):
                    raw = o.get("raw")
            if isinstance(raw, str):
                data = json.loads(raw)
                # Validar estructura mínima requerida
                required = ["report_id", "application_name", "summary", "prioritized_detectors"]
                if all(k in data for k in required):
                    return json.dumps(data, ensure_ascii=False)
        except Exception:
            pass
        try:
            if hasattr(result, "model_dump_json"):
                return result.model_dump_json()
        except Exception:
            pass
        # Si es un string JSON con campo 'raw', extraerlo
        try:
            if isinstance(result, str):
                obj = json.loads(result)
                if isinstance(obj, dict) and "raw" in obj and isinstance(obj["raw"], str):
                    data = json.loads(obj["raw"])
                    required = ["report_id", "application_name", "summary", "prioritized_detectors"]
                    if all(k in data for k in required):
                        return json.dumps(data, ensure_ascii=False)
        except Exception:
            pass
        return result


# Wrapper para compatibilidad con tests E2E legacy
def run_mcp_analysis(user_input: str, agent_trace_logger=None, llm_instance=None):
    """
    Ejecuta el análisis MCP de 3 agentes y retorna el reporte final en JSON (string).
    Permite inyectar un LLM simulado para testing.
    """
    logger = agent_trace_logger or logging.getLogger("mcp_analysis")
    crew = SecurityAnalysisCrew(agent_trace_logger=logger, llm_instance=llm_instance)
    result = crew.run(user_input)
    # Normalizar a dict JSON si es posible
    try:
        if hasattr(result, 'model_dump'):
            return result.model_dump()
    except Exception:
        pass
    try:
        if hasattr(result, 'dict'):
            return result.dict()
    except Exception:
        pass
    # Si es string JSON o wrapper con raw
    import json as _json
    if isinstance(result, str):
        try:
            obj = _json.loads(result)
            if isinstance(obj, dict):
                raw = obj.get('raw')
                if isinstance(raw, str):
                    try:
                        data = _json.loads(raw)
                        if isinstance(data, dict):
                            return data
                    except Exception:
                        pass
                return obj
        except Exception:
            pass
    # Último intento: si reporting_task.output fue serializado antes en SecurityAnalysisCrew.run como JSON string
    try:
        if isinstance(result, bytes):
            obj = _json.loads(result.decode('utf-8', errors='ignore'))
            if isinstance(obj, dict):
                return obj
    except Exception:
        pass
    return result
