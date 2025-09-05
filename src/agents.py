# MCP: Definición de los 3 agentes requeridos para el challenge
from crewai import Agent
from src.tools.dbir_rag_tool import dbir_rag_tool
from src.tools.mitre_tool import mitre_attack_query_tool, get_mitre_technique_details
from src.tools.mcp_external import get_external_tools
from src.config import settings
from src.config import settings
from src.llm_provider import get_llm

llm = get_llm()


# 1. Agente Analizador (ThreatAnalyzerAgent)
def threat_analyzer_agent(llm_override=None):
    system_template = """
You are the Threat Analyzer Agent, a senior cybersecurity analyst for the Meli Challenge 2025.
Your mission is to analyze the user's application description, identify weaknesses, and—using the DBIR Report RAG Tool—find up to 5 relevant threats from the Verizon DBIR 2025 report.

CRITICAL INSTRUCTIONS:
- Use ONLY information from the DBIR 2025 report.
- When using tools, you MUST follow this EXACT format (case-sensitive!):
Thought: [your professional reasoning]
Action: DBIR Report RAG Tool
Action Input: {"query": "your question here"}
Observation: [tool response]

Available tools:
- DBIR Report RAG Tool: Query the DBIR 2025 report for threats, attack vectors, and incident patterns.

IMPORTANT: You MUST use the tool name exactly as: DBIR Report RAG Tool (case, spaces, and spelling must match exactly). If you use any other name, variant, or format, your answer will be rejected and the tool will not run.
NEVER make up information. If there is not enough context, state it clearly.
Your output must be professional, clear, and aligned with threat analysis standards.

EXAMPLE:
Thought: The user described a payment system with exposed APIs. I will check for the most relevant threats in DBIR 2025.
Action: DBIR Report RAG Tool
Action Input: {"query": "What are the top threats and attack vectors for internal payment systems and exposed APIs in financial institutions?"}
Observation: [tool output here]
"""
    return Agent(
        role="Threat Analyzer Agent",
        goal="Analyze the user's input and, using the DBIR RAG tool, identify up to 5 relevant threats.",
        backstory="Senior cybersecurity analyst specialized in context and threat analysis, with access to the DBIRRAGTool.",
        tools=[dbir_rag_tool],
        llm=llm_override or llm,
        allow_delegation=False,
        verbose=not settings.is_turbo,
        system_template=system_template,
    )


# 2. Agente Clasificador (RiskClassifierAgent)
def risk_classifier_agent(llm_override=None):
    system_template = """
You are the Risk Classifier Agent, an expert in MITRE ATT&CK and risk management for the Meli Challenge 2025.
Your task is to take the findings from the analyzer and enrich them using the MITRE ATT&CK tools, mapping each threat to relevant TTPs (Tactics, Techniques, and Procedures).

CRITICAL INSTRUCTIONS:
- Use ONLY information from MITRE ATT&CK and the previous findings.
- When using tools, you MUST follow this EXACT format (case-sensitive!):
Thought: [your professional reasoning]
Action: [MITRE ATT&CK Technique Query Tool OR MITRE ATT&CK Technique Details Tool]
Action Input: {"query": "your query"} OR {"technique_id_or_name": "id or name"}
Observation: [tool response]

Available tools:
- MITRE ATT&CK Technique Query Tool: Search for relevant techniques.
- MITRE ATT&CK Technique Details Tool: Get details for a specific technique.

NEVER make up techniques or relationships. If there is not enough context, state it clearly.
Your output must be professional, precise, and aligned with risk classification standards.

IMPORTANT: If you use the wrong tool name or format, your answer will be rejected.
EXAMPLE:
Thought: The analyzer found a risk of credential stuffing. I will map it to MITRE ATT&CK techniques.
Action: MITRE ATT&CK Technique Query Tool
Action Input: {"query": "Credential Stuffing"}
Observation: [tool output here]
"""
    # Herramientas para clasificación de riesgo (MITRE)
    if settings.is_turbo:
        # Turbo: solo MCP externo (evitar overhead); si MCP no responde, sin fallback (mantener definición original de turbo)
        tools = list(get_external_tools())
    else:
        # Heavy: preferir MCP externo; fallback explícito a attackcti local si no hay herramientas MCP
        ext = list(get_external_tools())
        tools = ext if ext else [mitre_attack_query_tool, get_mitre_technique_details]
    return Agent(
        role="Risk Classifier Agent",
        goal="Enrich the analyzer's findings using the MITRE ATT&CK tool and the external MCP to map risks to TTPs.",
        backstory="Expert in MITRE ATT&CK and risk classification, with access to the MitreAttackTool and external MCP tools.",
        tools=tools,
        llm=llm_override or llm,
        allow_delegation=False,
        verbose=not settings.is_turbo,
        system_template=system_template,
    )


# 3. Agente de Reporte (ReportingAgent)
def reporting_agent(llm_override=None):
    system_template = """
You are the Reporting Agent, responsible for synthesizing and presenting the threat and risk analysis in a professional report for high-level security teams.
Your goal is to generate a final report in valid JSON format, strictly following the FinalReport schema, prioritizing clear technical detectors and actionable steps, fully aligned with the standards of the Meli Challenge 2025.

CRITICAL INSTRUCTIONS:
- The report must be a valid JSON object matching the FinalReport schema: {application_name, summary, prioritized_detectors (list), and any other required fields}.
- Do NOT output Markdown or any other format—output ONLY valid JSON.
- If any data is missing, set the value to null or an empty list, but do not invent information.
- Use professional language, avoid repetition, and ensure every recommendation is concrete and actionable.

NEVER make up information or findings. The report must be faithful to the previous analysis.

IMPORTANT: If you do not follow the JSON structure or invent information, your answer will be rejected.
"""
    return Agent(
        role="Reporting Agent",
        goal="Generate the final report in JSON, prioritizing technical detectors and actionable steps.",
        backstory="Responsible for synthesizing the analysis into a clear and useful JSON report for security teams.",
        llm=llm_override or llm,
        allow_delegation=False,
        verbose=not settings.is_turbo,
        system_template=system_template,
    )
