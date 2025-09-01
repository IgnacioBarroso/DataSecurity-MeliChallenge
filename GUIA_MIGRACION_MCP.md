Guía de Migración: De Crew Secuencial a Proceso Multi-Crew (MCP) en CrewAI
1. Introducción al Proceso Multi-Crew (MCP)
El Proceso Multi-Crew (MCP) es un patrón de diseño avanzado en CrewAI que permite a una Crew delegar tareas específicas a otra Crew entera. En lugar de tener un único equipo de agentes que lo hace todo de forma secuencial, MCP nos permite crear "equipos especializados" (sub-crews) y un "equipo gestor" (crew orquestadora) que sabe a qué equipo especializado delegar cada parte del trabajo.
Analogía: Imagina una compañía. En lugar de tener un solo equipo de 5 personas que hace marketing, ventas, desarrollo, soporte y finanzas, tienes departamentos especializados. El CEO (agente gestor) no hace el trabajo de marketing, sino que le asigna la tarea al "Departamento de Marketing" (una sub-crew).
Técnicamente, esto se logra tratando a una Crew completa como si fuera una Tool que puede ser asignada a un agente en otra Crew.
Ventajas para el MeliChallenge
* Modularidad y Cohesión: Agrupamos agentes con responsabilidades similares (ej. análisis de inteligencia de amenazas) en su propia crew. Esto hace el código más limpio y fácil de entender.
* Reusabilidad: Una crew especializada, como la de análisis de reportes, podría ser reutilizada en otros flujos de trabajo sin modificaciones.
* Escalabilidad: Es más fácil añadir nuevos agentes o especializaciones creando nuevas crews sin modificar las existentes.
* Testing Aislado: Puedes probar cada sub-crew de forma independiente, asegurando que cada "departamento" de tu sistema funcione correctamente por sí solo.
* Separación de Responsabilidades: El orquestador se enfoca en el flujo de alto nivel, mientras que las sub-crews se enfocan en la ejecución detallada de sus especialidades.
2. Arquitectura: De Secuencial a Jerárquica
Arquitectura Actual (Single-Crew)
Tu implementación actual en src/main_crew.py define una única ThreatAnalysisCrew con 5 agentes que ejecutan tareas en una cadena secuencial:
Input -> [Parsing -> ThreatIntel -> Vuln. Analysis -> Mitigation -> Reporting] -> Output
Esto es efectivo, pero monolítico. Si el proceso de reporte falla, toda la cadena se detiene. Si quieres mejorar el análisis de inteligencia, tienes que tocar la misma lógica central.
Arquitectura Propuesta (Multi-Crew)
Proponemos dividir el sistema en tres crews:
1. ThreatIntelCrew (Equipo de Inteligencia de Amenazas): Se especializa en la ingesta y el análisis inicial del reporte.
   * Agentes: ParsingAgent, ThreatIntelAgent.
   * Responsabilidad: Recibir el texto del reporte, extraer entidades clave (CVEs, TTPs) y enriquecerlas con información externa (MITRE ATT&CK, DBIR).
   * Output: Un informe de inteligencia de amenazas estructurado.
2. StrategyAndReportingCrew (Equipo de Estrategia y Reporte): Se especializa en analizar las implicaciones y generar el reporte final.
   * Agentes: VulnerabilityAnalysisAgent, MitigationStrategyAgent, ReportingAgent.
   * Responsabilidad: Tomar el informe de inteligencia, analizar las vulnerabilidades, proponer estrategias de mitigación y compilar todo en un informe final claro y conciso.
   * Output: El reporte final en formato Markdown.
3. SecurityAnalysisOrchestratorCrew (Equipo Orquestador): El equipo gestor que dirige el flujo de trabajo.
   * Agentes: ChiefSecurityOfficer (un nuevo agente gestor).
   * Herramientas (Tools): ThreatIntelCrew y StrategyAndReportingCrew.
   * Responsabilidad: Recibir el input inicial, delegar el análisis a ThreatIntelCrew, tomar el resultado y pasarlo a StrategyAndReportingCrew para la generación del reporte final.
El flujo sería así:
Input -> [Orchestrator] -> delega a -> [ThreatIntelCrew] -> devuelve resultado -> [Orchestrator] -> delega a -> [StrategyAndReportingCrew] -> devuelve resultado -> [Orchestrator] -> Output Final
3. Plan de Migración Detallado (Paso a Paso)
Paso 1: Crear un Nuevo Agente Orquestador
En src/agents.py, necesitamos definir el agente que liderará la crew principal.
# src/agents.py

# ... (mantener los agentes existentes)

from crewai import Agent
from crewai_tools import SerperDevTool, BaseTool # Asegurarse que BaseTool esté importado si se usan tools personalizadas

# ... (definiciones de agentes existentes) ...

class SecurityAnalysisAgents:
   # ... (métodos para los agentes existentes) ...

   def chief_security_officer(self):
       return Agent(
           role="Chief Security Officer (CSO)",
           goal="Orchestrate the security analysis process by delegating tasks to specialized teams and ensuring a comprehensive final report.",
           backstory=(
               "As a seasoned Chief Security Officer, you are an expert in managing cybersecurity teams and workflows. "
               "You don't execute the low-level analysis yourself; instead, you leverage your specialized teams—Threat Intelligence and Strategy—to"
               "produce a holistic security assessment. Your job is to manage the end-to-end process, ensuring seamless handoffs between teams."
           ),
           allow_delegation=True, # MUY IMPORTANTE: Permitir delegación a las sub-crews
           verbose=True,
       )


Paso 2: Refactorizar src/main_crew.py para Definir las Crews
Este es el cambio más grande. Reemplazaremos la clase ThreatAnalysisCrew por tres nuevas clases que representen nuestra nueva arquitectura.
Antes (Referencia):
# src/main_crew.py (versión actual simplificada)
class ThreatAnalysisCrew:
   def __init__(self, report_text):
       # ... inicialización de agentes y tareas
   
   def run(self):
       # ... crew.kickoff()

Después (Nueva Implementación):
# src/main_crew.py (NUEVA VERSIÓN)

from crewai import Crew, Process, Task
from src.agents import SecurityAnalysisAgents
from src.tools.mitre_tool import MitreAttackSearchTool
from src.tools.dbir_rag_tool import DBIRRAGTool
from src.llm_provider import llm

class SecurityCrews:
   def __init__(self, report_text: str):
       self.report_text = report_text
       self.agents = SecurityAnalysisAgents()
       self.tools = self._init_tools()

   def _init_tools(self):
       return {
           "mitre_tool": MitreAttackSearchTool(),
           "dbir_rag_tool": DBIRRAGTool(),
       }

   def threat_intel_crew(self):
       """
       Crew especializada en análisis de inteligencia de amenazas.
       """
       parser = self.agents.parsing_agent()
       threat_intel = self.agents.threat_intel_agent()
       
       # Tareas para esta crew
       parse_task = Task(
           description=f"Parse the following security report to identify key entities like CVEs, malware families, and TTPs. Report: \n\n{self.report_text}",
           expected_output="A structured list of identified entities (CVEs, TTPs, IoCs, etc.).",
           agent=parser,
       )
       
       threat_intel_task = Task(
           description="Using the parsed entities, enrich the data with context from MITRE ATT&CK and the DBIR report. Correlate TTPs with known threat actor groups and campaigns.",
           expected_output="An enriched intelligence report containing details on tactics, techniques, associated threat actors, and references from the knowledge bases.",
           agent=threat_intel,
           context=[parse_task]
       )
       
       return Crew(
           agents=[parser, threat_intel],
           tasks=[parse_task, threat_intel_task],
           process=Process.sequential,
           verbose=2,
           llm=llm,
       )

   def strategy_reporting_crew(self):
       """
       Crew especializada en análisis de vulnerabilidades, mitigación y reporte.
       """
       vuln_analyzer = self.agents.vulnerability_analysis_agent()
       mitigation_strategist = self.agents.mitigation_strategy_agent()
       reporter = self.agents.reporting_agent()

       # Tareas para esta crew
       vuln_analysis_task = Task(
           description="Based on the enriched threat intelligence report, analyze the identified vulnerabilities and TTPs to assess their potential impact on a corporate environment.",
           expected_output="A detailed impact assessment of the identified vulnerabilities and threats.",
           agent=vuln_analyzer,
       )

       mitigation_task = Task(
           description="Develop a set of actionable mitigation strategies and security controls to counter the identified threats and vulnerabilities. Prioritize recommendations based on impact and feasibility.",
           expected_output="A prioritized list of mitigation strategies, including technical and procedural recommendations.",
           agent=mitigation_strategist,
           context=[vuln_analysis_task]
       )

       reporting_task = Task(
           description="Compile all findings, analyses, and mitigation strategies into a comprehensive, well-structured final report in Markdown format. The report should be clear, concise, and targeted at security stakeholders.",
           expected_output="A final, polished security analysis report in Markdown format.",
           agent=reporter,
           context=[mitigation_task]
       )
       
       return Crew(
           agents=[vuln_analyzer, mitigation_strategist, reporter],
           tasks=[vuln_analysis_task, mitigation_task, reporting_task],
           process=Process.sequential,
           verbose=2,
           llm=llm
       )

   def orchestrator_crew(self):
       """
       Crew orquestadora que gestiona el flujo de trabajo y delega a las sub-crews.
       """
       cso_agent = self.agents.chief_security_officer()

       # Las sub-crews se convierten en herramientas para el orquestador
       threat_intel_crew = self.threat_intel_crew()
       strategy_reporting_crew = self.strategy_reporting_crew()

       # Tareas de delegación
       # El `description` ahora le pide al agente que USE la herramienta (la sub-crew)
       threat_intel_delegation_task = Task(
           description=f"Delegate the initial analysis of the security report to the Threat Intelligence Crew. Here is the report: \n\n{self.report_text}",
           expected_output="The complete and structured output from the Threat Intelligence Crew.",
           agent=cso_agent,
           tools=[threat_intel_crew], # Se pasa la crew como una herramienta
       )

       strategy_reporting_delegation_task = Task(
           description="Take the threat intelligence report and delegate it to the Strategy and Reporting Crew to perform vulnerability analysis, create mitigation strategies, and generate the final report.",
           expected_output="The final, comprehensive security report in Markdown format from the Strategy and Reporting Crew.",
           agent=cso_agent,
           context=[threat_intel_delegation_task],
           tools=[strategy_reporting_crew], # Se pasa la otra crew como herramienta
       )

       return Crew(
           agents=[cso_agent],
           tasks=[threat_intel_delegation_task, strategy_reporting_delegation_task],
           process=Process.sequential,
           verbose=2,
           llm=llm
       )

Paso 3: Actualizar el Servicio de la API
El servicio crew_service.py que es llamado por el router de FastAPI ahora debe instanciar y ejecutar la crew orquestadora en lugar de la antigua ThreatAnalysisCrew.
# api/services/crew_service.py

from src.main_crew import SecurityCrews  # Importar la nueva clase
import logging
import uuid

logger = logging.getLogger(__name__)

class CrewService:
   def run_crew(self, report_text: str) -> str:
       session_id = str(uuid.uuid4())
       logger.info(f"Starting crew run for session {session_id}")
       
       try:
           # 1. Instanciar la clase que contiene las definiciones de las crews
           security_crews_factory = SecurityCrews(report_text)
           
           # 2. Obtener la crew orquestadora
           orchestrator = security_crews_factory.orchestrator_crew()
           
           # 3. Ejecutar la crew orquestadora
           # El resultado de la última tarea de la crew orquestadora es el reporte final
           result = orchestrator.kickoff()
           
           logger.info(f"Crew run for session {session_id} finished successfully.")
           return result
       except Exception as e:
           logger.error(f"Error during crew run for session {session_id}: {e}", exc_info=True)
           # Considerar devolver un mensaje de error más específico a la API
           raise

Paso 4: Revisar y Adaptar Herramientas y Agentes
* Asignación de Herramientas: En la arquitectura original, las herramientas se pasaban a la Crew principal y estaban disponibles para todos los agentes. En la nueva arquitectura, es más limpio asignar herramientas solo a los agentes que las necesitan directamente. El chief_security_officer no necesita MitreAttackSearchTool, pero el ThreatIntelAgent sí.
* Asegúrate de que los agentes dentro de las sub-crews tengan acceso a las herramientas que necesitan. La forma más fácil es pasarlas al inicializar el agente.
Modificación Sugerida en src/agents.py para pasar herramientas:
# src/agents.py

class SecurityAnalysisAgents:
   def parsing_agent(self, llm): # Pasar llm es buena práctica
       # ...
   
   def threat_intel_agent(self, tools: list): # Aceptar una lista de herramientas
       return Agent(
           role="Threat Intelligence Analyst",
           # ...
           tools=tools, # Asignar las herramientas
           # ...
       )
   # ... otros agentes

Y en src/main_crew.py al crear la ThreatIntelCrew:
# src/main_crew.py

# ...
   def threat_intel_crew(self):
       # ...
       # Pasar las herramientas específicas al agente que las necesita
       threat_intel = self.agents.threat_intel_agent(tools=[self.tools["mitre_tool"], self.tools["dbir_rag_tool"]])
       # ...

4. Conclusión
Al seguir estos pasos, transformarás tu sistema de una estructura monolítica a una arquitectura MCP jerárquica y modular. Este nuevo diseño no solo es más elegante desde una perspectiva de ingeniería de software, sino que también alinea tu proyecto con las mejores prácticas para construir sistemas de agentes complejos y escalables con CrewAI.