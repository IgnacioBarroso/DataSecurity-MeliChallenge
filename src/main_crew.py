from crewai import Crew, Process, Task
from src.agents import (
    InputParsingAgent,
    RAGThreatAnalyzerAgent,
    RAGQualityValidatorAgent,
    TTPRiskClassifierAgent,
    ActionableReportingSpecialistAgent
)
from src.models import EcosystemContext, AnalyzedThreats, ClassifiedThreats, FinalSecurityReport

# --- Definición de Tareas ---

# Tarea 0: Parseo de Input
input_parsing_task = Task(
    description=(
        "Analiza el siguiente texto proporcionado por el usuario: '{user_input_text}'. "
        "Extrae la información clave y formatéala estrictamente como un objeto Pydantic 'EcosystemContext'. "
        "Tu única salida debe ser este objeto Pydantic."
    ),
    expected_output="Una única instancia del modelo Pydantic 'EcosystemContext' rellenada con la información extraída del texto de entrada.",
    agent=InputParsingAgent,
    output_pydantic=EcosystemContext
)

# Tarea 1: Analizar Amenazas con RAG
rag_analysis_task = Task(
    description=(
        "Tu primera misión es usar el contexto estructurado de la aplicación que has recibido. El nombre de la aplicación es '{application_name}' del contexto. "
        "Luego, utilizando la 'DBIR Report RAG Tool', formula una serie de preguntas clave al informe DBIR 2025 para encontrar "
        "las amenazas y patrones de ataque más relevantes para esa aplicación específica. "
        "Por ejemplo, si la app es una 'Plataforma de Gestión de Pagos', podrías preguntar: "
        "'¿Cuáles son los patrones de ataque más comunes contra aplicaciones financieras según el DBIR?', "
        "'¿Qué dice el DBIR sobre el abuso de privilegios en sistemas internos?', o "
        "'¿Estadísticas de ataques a aplicaciones web en el DBIR 2025'. "
        "Sintetiza la información recuperada para identificar los vectores de amenaza más plausibles."
    ),
    expected_output=(
        "Una instancia del modelo Pydantic 'AnalyzedThreats' que contenga una lista de objetos, "
        "donde cada objeto tiene los campos 'threat_vector' y 'justification'."
    ),
    agent=RAGThreatAnalyzerAgent,
    context=[input_parsing_task], # Depende de la tarea de parseo
    output_pydantic=AnalyzedThreats
)

# Tarea 2: Validación de Calidad de RAG
validation_task = Task(
    description=(
        "Revisa las amenazas identificadas por el Analista de Amenazas. "
        "Compara cada 'threat_vector' y 'justification' con el contexto de los "
        "fragmentos recuperados del DBIR que se te han pasado. "
        "Tu única salida debe ser la lista de amenazas original, sin cambios, "
        "solo si confirmas que están bien fundamentadas. Si encuentras una "
        "amenaza que no está respaldada por la evidencia, elimínala de la lista. "
        "Este es un paso de control de calidad crucial."
    ),
    expected_output=(
        "La misma instancia del modelo Pydantic 'AnalyzedThreats' recibida, "
        "potencialmente con menos amenazas si alguna fue invalidada. No añadas nada nuevo."
    ),
    agent=RAGQualityValidatorAgent,
    context=[rag_analysis_task],
    output_pydantic=AnalyzedThreats # La salida es del mismo tipo que la entrada
)

# Tarea 3: Clasificar TTPs y Riesgos
ttp_classification_task = Task(
    description=(
        "Tomar la lista de vectores de amenaza del paso anterior. Para cada uno, usar la herramienta de consulta "
        "de MITRE ATT&CK para encontrar las técnicas más relevantes. Luego, asignar un nivel de riesgo "
        "(Alto, Medio, Bajo) y proporcionar una justificación clara para esta clasificación."
    ),
    expected_output=(
        "Una instancia del modelo Pydantic 'ClassifiedThreats' que contenga una lista de amenazas "
        "enriquecidas con sus técnicas MITRE y su nivel de riesgo justificado."
    ),
    agent=TTPRiskClassifierAgent,
    context=[validation_task], # Depende de la tarea de validación
    output_pydantic=ClassifiedThreats
)

# Tarea 4: Generar Reporte Final
reporting_task = Task(
    description=(
        "Compilar toda la información analizada y clasificada en un informe de seguridad final y profesional. "
        "El informe debe priorizar y presentar únicamente los 5 detectores más críticos. "
        "Para cada detector, redacta un nombre claro, resume el riesgo, las técnicas MITRE asociadas "
        "y, lo más importante, proporciona una lista de 'actionable_steps' (pasos accionables) "
        "que los equipos de seguridad puedan seguir para implementar el detector."
    ),
    expected_output=(
        "Una única instancia del modelo Pydantic 'FinalSecurityReport' que contenga todos los campos "
        "requeridos, listo para ser devuelto por la API."
    ),
    agent=ActionableReportingSpecialistAgent,
    context=[ttp_classification_task],
    output_pydantic=FinalSecurityReport
)

# Ensamblaje del Crew
security_analysis_crew = Crew(
    agents=[InputParsingAgent, RAGThreatAnalyzerAgent, RAGQualityValidatorAgent, TTPRiskClassifierAgent, ActionableReportingSpecialistAgent],
    tasks=[input_parsing_task, rag_analysis_task, validation_task, ttp_classification_task, reporting_task],
    process=Process.sequential,
    verbose=2
)