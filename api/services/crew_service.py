
import uuid
import logging
from src.main_crew import security_analysis_crew
from src.models import FinalSecurityReport
from src.logging_config import setup_session_logging

def run_security_analysis(user_input_text: str) -> FinalSecurityReport:
    # Validación temprana del input
    if not user_input_text or not isinstance(user_input_text, str) or user_input_text.strip() == "":
        raise ValueError("El texto de entrada para el análisis no puede estar vacío o ser inválido.")

    session_id = str(uuid.uuid4())
    setup_session_logging(session_id)
    inputs = {
        "user_input_text": user_input_text,
        "session_id": session_id
    }

    logging.info(f"Lanzando el Crew de análisis para la sesión {session_id}...")
    
    try:
        result = security_analysis_crew.kickoff(inputs=inputs)
        logging.info(f"El Crew para la sesión {session_id} ha finalizado exitosamente.")

        if not isinstance(result, FinalSecurityReport):
            logging.error(f"Resultado inesperado del crew para la sesión {session_id}: el tipo fue {type(result)} en lugar de FinalSecurityReport.")
            raise ValueError("El análisis no pudo generar un reporte con el formato válido.")

        result.report_id = session_id
        return result

    except Exception as e:
        logging.error(f"Ocurrió un error catastrófico durante la ejecución del crew para la sesión {session_id}: {e}", exc_info=True)
        raise
