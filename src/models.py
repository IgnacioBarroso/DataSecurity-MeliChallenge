from pydantic import BaseModel, Field
from typing import List, Optional

# Modelo para un único vector de amenaza identificado por el Agente Analizador.
class ThreatVector(BaseModel):
    threat_vector: str = Field(description="Descripción concisa y clara del vector de amenaza identificado.")
    justification: str = Field(description="Explicación detallada que vincula el vector de amenaza con evidencia del informe DBIR y el contexto específico de la aplicación.")

# Modelo para la lista de amenazas que el Agente Analizador pasa al Clasificador.
class AnalyzedThreats(BaseModel):
    threats: List[ThreatVector]

# Modelo para representar una técnica específica del framework MITRE ATT&CK.
class MitreTechnique(BaseModel):
    id: str = Field(description="El ID único de la técnica MITRE ATT&CK, por ejemplo, 'T1078'.")
    name: str = Field(description="El nombre oficial de la técnica MITRE ATT&CK.")
    description: Optional[str] = Field(description="Una breve descripción de la técnica MITRE.")

# Modelo para una amenaza que ha sido enriquecida por el Agente Clasificador.
class ClassifiedThreat(BaseModel):
    threat_vector: str = Field(description="Descripción del vector de amenaza, heredado del análisis inicial.")
    justification: str = Field(description="Justificación inicial, heredada del análisis.")
    mitre_techniques: List[MitreTechnique] = Field(description="Lista de técnicas MITRE ATT&CK asociadas a este vector de amenaza.")
    risk_level: str = Field(description="Nivel de riesgo asignado: 'Alto', 'Medio' o 'Bajo'.")
    risk_rationale: str = Field(description="Justificación clara y concisa para la clasificación del riesgo asignado.")

# Modelo para la lista de amenazas clasificadas que se pasa al Agente Reportero.
class ClassifiedThreats(BaseModel):
    classified_threats: List[ClassifiedThreat]

# Modelo para una recomendación accionable final, que forma parte del reporte.
class ActionableRecommendation(BaseModel):
    priority: int = Field(description="La prioridad numérica del detector (ej. 1 para el más importante).")
    detector_name: str = Field(description="Un nombre claro y sugerido para el nuevo mecanismo detectivo.")
    risk_level: str = Field(description="El nivel de riesgo asociado ('Alto', 'Medio', 'Bajo').")
    threat_vector: str = Field(description="El vector de amenaza que este detector busca mitigar.")
    mitre_techniques: List[MitreTechnique] = Field(description="Técnicas MITRE ATT&CK cubiertas por este detector.")
    rationale: str = Field(description="Resumen del análisis de riesgo y la justificación para la creación de este detector.")
    actionable_steps: List[str] = Field(description="Lista de pasos concretos y técnicos para implementar el detector (ej. 'Crear regla de SIEM', 'Configurar rate limiting').")

# Modelo para el contexto de la aplicación, extraído del input del usuario
class EcosystemContext(BaseModel):
    application_name: str = Field(description="Nombre de la aplicación, ej. 'Internal Payments Hub'.")
    usage_description: str = Field(description="Descripción detallada del uso y funcionalidades de la aplicación.")
    exposed_apis: List[str] = Field(description="Lista de APIs internas o externas expuestas o consumidas por el sistema.")
    technologies: List[str] = Field(description="Stack tecnológico, ej. 'Python+Django', 'PostgreSQL', 'React'.")
    current_controls: List[str] = Field(description="Controles de seguridad que ya están implementados.")

# Modelo final para el reporte de seguridad completo generado por el Agente Reportero.
class FinalSecurityReport(BaseModel):
    report_id: str = Field(description="Un ID único para esta ejecución del análisis.")
    application_name: str = Field(description="El nombre de la aplicación analizada.")
    summary: str = Field(description="Un resumen ejecutivo del reporte, destacando los hallazgos más importantes.")
    prioritized_detectors: List[ActionableRecommendation] = Field(description="La lista de los 5 detectores más importantes a desarrollar.")

# Modelo para el input del servicio, que es más simple que el request de la API
class SecurityReportInput(BaseModel):
    text: str
