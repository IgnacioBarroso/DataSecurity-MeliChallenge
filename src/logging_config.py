
# src/logging_config.py
import logging
import sys
from pathlib import Path

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

def setup_session_logging(session_id: str):
    """Configura un logger para una sesión específica, escribiendo en un archivo único."""
    log_file = LOGS_DIR / f"session_{session_id}.log"
    
    # Prevenir duplicación de handlers si se llama varias veces
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
            
    # Configuración básica
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - (%(module)s:%(funcName)s) - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"Logging configurado para la sesión {session_id}. Archivo: {log_file}")
