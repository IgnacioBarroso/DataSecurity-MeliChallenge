from src.config import load_config
from api.app import create_app

# Cargar configuración al inicio
load_config()
app = create_app()