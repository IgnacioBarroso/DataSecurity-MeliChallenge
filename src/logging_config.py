
import logging
import sys
from pathlib import Path
import json

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        if hasattr(record, 'session_id'):
            log_record['session_id'] = record.session_id
        if hasattr(record, 'agent_name'):
            log_record['agent_name'] = record.agent_name
        if hasattr(record, 'task_name'):
            log_record['task_name'] = record.task_name
        if hasattr(record, 'input_data'):
            log_record['input_data'] = record.input_data
        if hasattr(record, 'output_data'):
            log_record['output_data'] = record.output_data
        return json.dumps(log_record)

def setup_session_logging(session_id: str):
    """Configura un logger para una sesión específica, escribiendo en un archivo único."""
    log_file = LOGS_DIR / f"session_{session_id}.log"
    
    # Prevenir duplicación de handlers si se llama varias veces
    logger = logging.getLogger()
    # Remove all handlers to prevent duplication across sessions
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

def setup_agent_trace_logging(session_id: str):
    """
    Configura un logger específico para trazas de agentes en formato JSON.
    """
    trace_log_file = LOGS_DIR / f"session_{session_id}_trace.json"
    
    trace_logger = logging.getLogger(f'agent_trace_{session_id}')
    trace_logger.setLevel(logging.INFO)
    trace_logger.propagate = False # Evitar que los logs se propaguen al logger root

    # Prevenir duplicación de handlers
    if not trace_logger.handlers:
        file_handler = logging.FileHandler(trace_log_file)
        file_handler.setFormatter(JsonFormatter())
        trace_logger.addHandler(file_handler)

    return trace_logger
