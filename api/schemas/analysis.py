from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    """Modelo para la solicitud de análisis: solo el input del usuario."""

    user_input: str


class AnalysisResponse(BaseModel):
    """Modelo para la respuesta: reporte final y session_id opcional."""

    report: str
    session_id: str | None = None
