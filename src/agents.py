# MCP: Definición de los 3 agentes requeridos para el challenge
from crewai import Agent
from src.tools.dbir_rag_tool import dbir_rag_tool
from src.tools.mitre_tool import mitre_attack_query_tool, get_mitre_technique_details
from src.llm_provider import get_llm

llm = get_llm()


# 1. Agente Analizador (ThreatAnalyzerAgent)
def threat_analyzer_agent(llm_override=None):
    return Agent(
        role="Threat Analyzer Agent",
        goal="Analizar el input del usuario y, usando la herramienta RAG DBIR, identificar hasta 5 amenazas relevantes.",
        backstory="Especialista en análisis de contexto y amenazas, con acceso a la herramienta DBIRRAGTool.",
        tools=[dbir_rag_tool],
        llm=llm_override or llm,
        allow_delegation=False,
        verbose=True,
    )


# 2. Agente Clasificador (RiskClassifierAgent)
def risk_classifier_agent(llm_override=None):
    return Agent(
        role="Risk Classifier Agent",
        goal="Enriquecer los hallazgos del analizador usando la herramienta MITRE ATT&CK para mapear riesgos a TTPs.",
        backstory="Especialista en MITRE ATT&CK y clasificación de riesgos, con acceso a la herramienta MitreAttackTool.",
        tools=[mitre_attack_query_tool, get_mitre_technique_details],
        llm=llm_override or llm,
        allow_delegation=False,
        verbose=True,
    )


# 3. Agente de Reporte (ReportingAgent)
def reporting_agent(llm_override=None):
    return Agent(
        role="Reporting Agent",
        goal="Generar el reporte final en Markdown, priorizando los detectores y accionables técnicos.",
        backstory="Responsable de sintetizar el análisis en un informe claro y útil para equipos de seguridad.",
        llm=llm_override or llm,
        allow_delegation=False,
        verbose=True,
    )
