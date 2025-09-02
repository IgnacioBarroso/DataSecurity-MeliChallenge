"""
Implementación de la arquitectura MCP (Model-Controller-Plane) para CrewAI.

Este módulo define el patrón de orquestación secuencial requerido por el challenge,
_donde el output de una sub-crew se convierte en el input de la siguiente.
"""

from crewai import Crew, Process, Task, Agent
from src.tools.dbir_rag_tool import dbir_rag_tool
from src.tools.mitre_tool import mitre_attack_query_tool, get_mitre_technique_details
from src.llm_provider import get_llm
from src.models import ThreatFindings, EnrichedFindings, FinalReport
import logging
from src.agents import threat_analyzer_agent, risk_classifier_agent, reporting_agent


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
        # 1. Task: Análisis de amenazas
        analysis_task = Task(
            description=f"Analiza el input del usuario y encuentra hasta 5 amenazas relevantes usando DBIR: {user_input}",
            expected_output="Lista de amenazas (ThreatFinding) en JSON.",
            agent=self.analyzer,
            output_pydantic=ThreatFindings,
        )
        # 2. Task: Clasificación de riesgos
        classification_task = Task(
            description="Enriquece los hallazgos con MITRE ATT&CK y clasifica el riesgo.",
            expected_output="Lista de amenazas enriquecidas (EnrichedFinding) en JSON.",
            agent=self.classifier,
            context=[analysis_task],
            output_pydantic=EnrichedFindings,
        )
        # 3. Task: Generación de reporte final
        reporting_task = Task(
            description="Genera el reporte final en Markdown con detectores priorizados y accionables.",
            expected_output="Reporte final (FinalReport) en JSON.",
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
        result = crew.kickoff()
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
    import json
    return json.dumps(result) if not isinstance(result, str) else result
