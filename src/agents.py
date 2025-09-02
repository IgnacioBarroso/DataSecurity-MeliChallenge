from crewai import Agent 
from src.tools.dbir_rag_tool import dbir_rag_tool
from src.tools.mitre_tool import mitre_attack_query_tool,get_mitre_technique_details
import os

# Configuración del LLM
from src.llm_provider import get_llm

class SecurityAnalysisAgents:
    def __init__(self):
        self.llm = get_llm()

    def parsing_agent(self):
        return Agent(
            role='Especialista en Extracción de Entidades y Estructuración de Datos',
            goal=(
                "Procesar el texto en lenguaje natural o semi-estructurado proporcionado por el usuario "
                "y convertirlo en un objeto JSON estructurado que siga el modelo Pydantic 'EcosystemContext'."
            ),
            backstory=(
                "Eres un experto en Procesamiento de Lenguaje Natural (NLP) con la habilidad de identificar "
                "y extraer información clave de textos no estructurados. Tu única función es leer la descripción "
                "de una aplicación y mapear sus detalles (nombre, uso, tecnologías, APIs, controles) a un "
                "formato JSON predefinido y validado. No realizas ningún tipo de análisis de seguridad, solo "
                "estructuras la información de entrada para que los siguientes agentes puedan trabajar de manera eficiente y precisa."
            ),
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

    def threat_intel_agent(self, tools: list):
        return Agent(
            role='Analista Senior de Inteligencia de Amenazas de Ciberseguridad',
            goal=(
                "Analizar el contexto de una aplicación y, utilizando la herramienta de consulta del DBIR, "
                "identificar y extraer los vectores de amenaza más relevantes y aplicables del informe."
            ),
            backstory=(
                "Eres un experto en el análisis de reportes de inteligencia de amenazas, con una habilidad "
                "especial para conectar tendencias globales con vulnerabilidades de sistemas específicos. "
                "Tu principal herramienta es un sistema RAG avanzado que te permite interrogar el informe "
                "DBIR 2025 para obtener la información más precisa. Tu misión es filtrar el ruido y "
                "enfocarte únicamente en las amenazas que representan un riesgo real para la aplicación bajo análisis."
            ),
            tools=tools,
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

    def ttp_risk_classifier_agent(self):
        return Agent(
            role='Especialista en Evaluación de Riesgos y MITRE ATT&CK',
            goal=(
                "Mapear los vectores de amenaza identificados a técnicas específicas del framework MITRE ATT&CK, "
                "evaluar su riesgo y justificar la clasificación."
            ),
            backstory=(
                "Con una profunda experiencia en el framework MITRE ATT&CK, tu especialidad es traducir "
                "amenazas de alto nivel en tácticas, técnicas y procedimientos (TTPs) concretos. "
                "Utilizas tu conocimiento y herramientas para buscar en la base de datos de ATT&CK, "
                "asignar un nivel de riesgo (Alto, Medio, Bajo) a cada amenaza y proporcionar una "
                "justificación sólida basada en el impacto potencial en un entorno corporativo."
            ),
            tools=[mitre_attack_query_tool, get_mitre_technique_details],
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

    def actionable_reporting_specialist_agent(self):
        return Agent(
            role='Gerente Senior de Programas de Seguridad',
            goal=(
                "Sintetizar el análisis técnico en un informe de seguridad claro, conciso y accionable, "
                "priorizando los 5 detectores más críticos y proporcionando recomendaciones concretas."
            ),
            backstory=(
                "Eres un puente entre el análisis técnico profundo y los equipos de ingeniería de seguridad. "
                "Tu habilidad reside en transformar datos complejos en planes de acción. No te enfocas en "
                "la investigación, sino en la comunicación efectiva. Tomas la lista de amenazas clasificadas "
                "y produces un informe final que es inmediatamente útil para que los equipos comiencen a "
                "desarrollar nuevos mecanismos de detección."
            ),
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

    def rag_quality_validator_agent(self):
        return Agent(
            role='Auditor de Calidad de IA y Trazabilidad',
            goal=(
                "Verificar que las conclusiones del Analista de Amenazas estén directamente "
                "respaldadas por la evidencia recuperada del informe DBIR, asegurando la "
                "máxima fiabilidad y evitando alucinaciones."
            ),
            backstory=(
                "Eres un auditor meticuloso especializado en la validación de sistemas de IA. "
                "Tu función no es generar nuevo conocimiento, sino actuar como un control de calidad. "
                "Recibes los fragmentos de texto recuperados por el sistema RAG y las amenazas "
                "identificadas por el analista. Tu única tarea es comparar ambos y confirmar que "
                "cada amenaza y su justificación se derivan lógicamente de la evidencia proporcionada. "
                "Tu aprobación es el sello de calidad que garantiza que el análisis es confiable y está basado en hechos."
            ),
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

    def mitigation_strategy_agent(self):
        return Agent(
            role='Especialista en Estrategias de Mitigación',
            goal=(
                "Desarrollar estrategias de mitigación y controles de seguridad accionables "
                "para contrarrestar las amenazas y vulnerabilidades identificadas, priorizando "
                "las recomendaciones basadas en el impacto y la viabilidad."
            ),
            backstory=(
                "Eres un arquitecto de seguridad con experiencia en el diseño e implementación "
                "de soluciones defensivas. Tu enfoque es práctico y orientado a resultados, "
                "transformando los análisis de amenazas en planes concretos para fortalecer "
                "la postura de seguridad de una organización."
            ),
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

    def chief_security_officer(self):
        return Agent(
            role="Chief Security Officer (CSO)",
            goal="Orchestrate the security analysis process by delegating tasks to specialized teams and ensuring a comprehensive final report.",
            backstory=(
                "As a seasoned Chief Security Officer, you are an expert in managing cybersecurity teams and workflows. "
                "You don't execute the low-level analysis yourself; instead, you leverage your specialized teams—Threat Intelligence and Strategy—to"
                "produce a holistic security assessment. Your job is to manage the end-to-end process, ensuring seamless handoffs between teams."
            ),
            allow_delegation=True,
            verbose=True,
            llm=self.llm
        )
