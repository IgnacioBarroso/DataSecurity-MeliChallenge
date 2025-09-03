# Modelos Pydantic para el flujo MCP de 3 agentes
from pydantic import BaseModel, Field
from typing import List, Optional

# Input estándar para el análisis (restaurado para compatibilidad con tests y servicios)
class SecurityReportInput(BaseModel):
    text: str


# 1. Output del Analizador (ThreatFinding)
class ThreatFinding(BaseModel):
    detector_name: str = Field(
        description="Nombre sugerido para el detector o amenaza identificada."
    )
    risk_description: str = Field(
        description="Descripción del riesgo o debilidad encontrada."
    )
    initial_severity: str = Field(
        description="Severidad inicial estimada: 'Alto', 'Medio', 'Bajo'."
    )


class ThreatFindings(BaseModel):
    findings: List[ThreatFinding]


# 2. Output del Clasificador (EnrichedFinding)
class MitreTTP(BaseModel):
    id: str = Field(description="ID de la técnica MITRE ATT&CK, ej. 'T1110'.")
    name: str = Field(description="Nombre de la técnica MITRE ATT&CK.")
    description: Optional[str] = Field(description="Descripción breve de la técnica.")


class EnrichedFinding(ThreatFinding):
    mitre_ttps: List[MitreTTP] = Field(description="Lista de TTPs MITRE asociadas.")
    risk_level: str = Field(
        description="Nivel de riesgo final: 'Alto', 'Medio', 'Bajo'."
    )
    risk_rationale: str = Field(
        description="Justificación para la clasificación del riesgo."
    )


class EnrichedFindings(BaseModel):
    findings: List[EnrichedFinding]


# 3. Output del Reporte Final (FinalReport)
class ActionableStep(BaseModel):
    step: str


class FinalReport(BaseModel):
    report_id: str = Field(description="ID único de la sesión de análisis.")
    application_name: str = Field(description="Nombre de la aplicación analizada.")
    summary: str = Field(description="Resumen ejecutivo del reporte.")
    prioritized_detectors: List[dict] = Field(
        description="Detectores priorizados con detalles, TTPs, riesgos y pasos accionables."
    )
