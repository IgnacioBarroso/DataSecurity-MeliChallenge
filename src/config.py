import os
from dotenv import load_dotenv

# Carga las variables de entorno desde un archivo .env
# Es útil para mantener las claves de API y otras configuraciones seguras y fuera del código fuente.
load_dotenv()

# Obtiene la clave de API de Google desde las variables de entorno.
# Si no se encuentra, se utiliza un valor predeterminado para evitar errores,
# aunque la aplicación fallará si se intenta usar la API sin una clave válida.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_DEFAULT_API_KEY")

# Variable para configurar el nombre del modelo de LLM a utilizar.
# Esto permite cambiar fácilmente entre diferentes modelos (ej. gemini-1.5-flash, gemini-1.5-pro).
LLM_MODEL_NAME = "gemini-1.5-pro-latest"

# --- Constantes del Sistema RAG ---
CHROMA_DB_PATH = "vector_db"
COLLECTION_NAME = "dbir_2025"