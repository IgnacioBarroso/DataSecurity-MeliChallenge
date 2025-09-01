
# src/llm_provider.py
import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama
from src.config import GEMINI_API_KEY, LLM_MODEL_NAME

def get_llm():
    """
    Fábrica de LLMs que lee las variables de entorno para determinar qué modelo instanciar.
    Permite cambiar dinámicamente entre un LLM en la nube (Google Gemini) y uno local (Ollama).

    Returns:
        Una instancia de un modelo de lenguaje compatible con LangChain/CrewAI.
    """
    provider = os.getenv("LLM_PROVIDER", "google").lower()
    
    logging.info(f"Seleccionando proveedor de LLM: {provider}")

    if provider == "local":
        try:
            ollama_base_url = os.getenv("OLLAMA_BASE_URL")
            ollama_model = os.getenv("OLLAMA_MODEL")
            
            if not ollama_base_url or not ollama_model:
                raise ValueError("Las variables de entorno OLLAMA_BASE_URL y OLLAMA_MODEL son requeridas para el proveedor local.")

            logging.info(f"Inicializando LLM local (Ollama) con el modelo '{ollama_model}' en '{ollama_base_url}'")
            llm = Ollama(
                base_url=ollama_base_url,
                model=ollama_model,
                # Puedes añadir más parámetros de configuración aquí si es necesario
            )
            return llm
        except Exception as e:
            logging.error(f"Error al inicializar Ollama. Asegúrate de que el servidor de Ollama esté en ejecución y sea accesible. Error: {e}")
            logging.warning("Cambiando al proveedor por defecto (Google) debido a un error de configuración local.")
            # Fallback to Google if local setup fails
    
    # Por defecto o en caso de fallback, usar Google Gemini
    if GEMINI_API_KEY == "YOUR_API_KEY_DE_GEMINI" or not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY no está configurada. Por favor, añádela a tu archivo .env")

    logging.info("Inicializando LLM en la nube (Google Gemini) con el modelo 'gemini-1.5-pro-latest'")
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL_NAME,
        verbose=True,
        temperature=0.1,
        google_api_key=GEMINI_API_KEY
    )
    return llm
