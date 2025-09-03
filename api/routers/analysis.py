"""
Router para el endpoint de análisis de seguridad.
"""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
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


@router.post(
    "/analyze-upload",
    response_model=AnalysisResponse,
    summary="Analiza contexto recibido como archivo .txt o texto en formulario",
    description=(
        "Recibe un archivo .txt via multipart/form-data o un campo de texto 'user_input'"
        " y ejecuta el pipeline MCP devolviendo el reporte final en JSON."
    ),
)
async def analyze_ecosystem_upload(
    file: UploadFile | None = File(default=None),
    user_input: str | None = Form(default=None),
):
    try:
        text: str | None = None
        if file is not None:
            if file.content_type not in ("text/plain", "application/octet-stream"):
                raise HTTPException(status_code=415, detail="Solo se aceptan archivos .txt")
            content = await file.read()
            try:
                text = content.decode("utf-8")
            except Exception:
                # intento de latin-1 si no es UTF-8
                text = content.decode("latin-1", errors="ignore")
        elif user_input is not None:
            text = user_input

        if not text or not text.strip():
            raise HTTPException(status_code=422, detail="El input no puede estar vacío.")

        result = await crew_service.run_analysis_crew(text)
        return AnalysisResponse(
            report_json=result.get("report_json", "{}"),
            session_id=result.get("session_id"),
        )
    except HTTPException:
        raise
    except Exception as e:
        import logging as _logging
        _logging.critical(
            f"Error inesperado en el endpoint /analyze-upload: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno inesperado en el servidor de análisis (upload).",
        )
