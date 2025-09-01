from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    """Modelo para la solicitud de análisis, esperando el input del usuario en texto plano."""
    user_input_text: str