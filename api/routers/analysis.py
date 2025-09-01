import logging
from fastapi import APIRouter, HTTPException
from api.services import crew_service
from api.schemas.analysis import AnalysisRequest
from src.models import FinalSecurityReport

router = APIRouter()

@router.post(
    "/analyze",
    response_model=FinalSecurityReport,
    summary="Ejecutar análisis de seguridad",
    description="Inicia el pipeline de agentes de IA para analizar el contexto de una aplicación y generar un reporte de seguridad."
)
def analyze_ecosystem(request: AnalysisRequest):
    """
    Endpoint para recibir el contexto de la aplicación y devolver el reporte de seguridad.
    """
    try:
        logging.info("Recibida solicitud de análisis...")
        report = crew_service.run_security_analysis(request.user_input_text)
        logging.info(f"Análisis completado. Devolviendo reporte ID: {report.report_id}")
        return report
    except ValueError as ve:
        # Error conocido y manejado, como un resultado inválido del crew.
        logging.error(f"Error de validación durante el análisis: {ve}")
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        # Error inesperado y no controlado.
        logging.critical(f"Error inesperado en el endpoint /analyze: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error interno inesperado en el servidor de análisis.")