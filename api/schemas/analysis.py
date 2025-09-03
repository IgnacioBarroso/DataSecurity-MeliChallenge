from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    """Modelo para la solicitud de análisis: solo el input del usuario."""

    user_input: str


class AnalysisResponse(BaseModel):
    """Modelo para la respuesta: reporte final en JSON y session_id opcional."""
    report_json: str
    session_id: str | None = None
