"""
Implementación de la arquitectura MCP (Model-Controller-Plane) para CrewAI.

Este módulo define el patrón de orquestación secuencial requerido por el challenge,
_donde el output de una sub-crew se convierte en el input de la siguiente.
"""
from crewai import Crew, Process, Task, Agent
from src.tools.dbir_rag_tool import dbir_rag_tool
from src.tools.mitre_tool import mitre_attack_query_tool, get_mitre_technique_details
from src.llm_provider import get_llm
from src.models import EcosystemContext, AnalyzedThreats, ClassifiedThreats, FinalSecurityReport
import logging # Importar logging para el tipo de dato del logger

# --- Inicialización Singleton --- 
# Se inicializan una sola vez y se reutilizan en toda la aplicación para eficiencia.
llm = get_llm()

# --- Definición de Agentes --- 
# Los agentes se definen aquí para ser reutilizados por diferentes crews.
parsing_agent = Agent(
    role="Input Parsing Agent",
    goal="Parsear el input del usuario y estructurarlo como EcosystemContext.",
    backstory="Especialista en extracción de entidades y estructuración de datos.",
    llm=llm,
    allow_delegation=False,
    verbose=True
)

threat_intel_agent = Agent(
    role="Threat Intelligence Analyst",
    goal="Analizar el contexto y extraer amenazas relevantes usando DBIR.",
    backstory="Experto en análisis de inteligencia de amenazas y uso de RAG DBIR.",
    tools=[dbir_rag_tool],
    llm=llm,
    allow_delegation=False,
    verbose=True
)

mitre_classifier_agent = Agent(
    role="MITRE ATT&CK Classifier",
    goal="Mapear amenazas a técnicas MITRE ATT&CK y clasificar riesgos.",
    backstory="Especialista en MITRE ATT&CK y clasificación de riesgos.",
    tools=[mitre_attack_query_tool, get_mitre_technique_details],
    llm=llm,
    allow_delegation=False,
    verbose=True
)

reporting_agent = Agent(
    role="Reporting Specialist",
    goal="Generar el reporte final con detectores, riesgos y accionables.",
    backstory="Responsable de sintetizar el análisis en un informe claro y útil.",
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# --- Definición de Sub-Crews Especializadas ---
def create_threat_intel_crew(user_input: str, agent_trace_logger: logging.Logger) -> Crew:
    parse_task = Task(
        description=f"Parsea el siguiente input de usuario y estructúralo como EcosystemContext: {user_input}",
        expected_output="Un objeto JSON que cumpla con el modelo Pydantic EcosystemContext.",
        agent=parsing_agent,
        output_pydantic=EcosystemContext
    )
    threat_task = Task(
        description="Analiza el contexto estructurado y extrae hasta 5 amenazas relevantes usando el informe DBIR.",
        expected_output="Una lista de amenazas en formato JSON que cumpla con el modelo Pydantic AnalyzedThreats.",
        agent=threat_intel_agent,
        context=[parse_task],
        output_pydantic=AnalyzedThreats
    )
    return Crew(agents=[parsing_agent, threat_intel_agent], tasks=[parse_task, threat_task], process=Process.sequential, verbose=True, agent_trace_logger=agent_trace_logger)

def create_mitre_classification_crew(agent_trace_logger: logging.Logger) -> Crew:
    mitre_task = Task(
        description="Mapea las amenazas identificadas a técnicas MITRE ATT&CK y clasifica su riesgo.",
        expected_output="Una lista de amenazas clasificadas en formato JSON que cumpla con el modelo Pydantic ClassifiedThreats.",
        agent=mitre_classifier_agent,
        output_pydantic=ClassifiedThreats
    )
    return Crew(agents=[mitre_classifier_agent], tasks=[mitre_task], process=Process.sequential, verbose=True, agent_trace_logger=agent_trace_logger)

def create_reporting_crew(agent_trace_logger: logging.Logger) -> Crew:
    report_task = Task(
        description="Genera el reporte final de seguridad con detectores, riesgos y accionables en formato Markdown.",
        expected_output="Un reporte de seguridad en formato JSON que cumpla con el modelo Pydantic FinalSecurityReport.",
        agent=reporting_agent,
        output_pydantic=FinalSecurityReport
    )
    return Crew(agents=[reporting_agent], tasks=[report_task], process=Process.sequential, verbose=True, agent_trace_logger=agent_trace_logger)

# --- Orquestador Principal (MCP) ---
def run_mcp_analysis(user_input: str, agent_trace_logger: logging.Logger) -> str:
    """
    Función principal que orquesta la ejecución secuencial de las sub-crews.
    """
    # 1. Crew de Inteligencia de Amenazas
    threat_intel_crew = create_threat_intel_crew(user_input, agent_trace_logger)
    threat_output = threat_intel_crew.kickoff()

    # 2. Crew de Clasificación MITRE
    # El output de la crew anterior (un objeto Pydantic) se pasa como diccionario al input de la siguiente.
    mitre_crew = create_mitre_classification_crew(agent_trace_logger)
    mitre_output = mitre_crew.kickoff(inputs=threat_output.model_dump())

    # 3. Crew de Reporte Final
    reporting_crew = create_reporting_crew(agent_trace_logger)
    report_output = reporting_crew.kickoff(inputs=mitre_output.model_dump())

    # Devuelve el resultado final como un string JSON.
    return report_output.model_dump_json()
