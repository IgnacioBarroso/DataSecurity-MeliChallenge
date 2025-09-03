"""
Router para el endpoint de análisis de seguridad.
"""

import logging
from fastapi import APIRouter, HTTPException
from api.services import crew_service

from api.schemas.analysis import AnalysisRequest, AnalysisResponse

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Ejecutar análisis de seguridad con arquitectura MCP",
    description="Inicia el pipeline de agentes de IA (arquitectura MCP) para analizar el contexto de una aplicación y generar un reporte de seguridad.",
)
async def analyze_ecosystem(request: AnalysisRequest):
    """
    Endpoint asíncrono para recibir el contexto de la aplicación y devolver el reporte de seguridad.
    """
    try:
        logging.info("Recibida solicitud de análisis para la arquitectura MCP...")
        result = await crew_service.run_analysis_crew(request.user_input)
        logging.info(f"Análisis MCP completado.")
        # Adaptar el resultado para AnalysisResponse
        return AnalysisResponse(
            report_json=result.get("report_json", "{}"),
            session_id=result.get("session_id")
        )
    except ValueError as ve:
        logging.error(f"Input inválido: {ve}")
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logging.critical(
            f"Error inesperado en el endpoint /analyze: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno inesperado en el servidor de análisis.",
        )
