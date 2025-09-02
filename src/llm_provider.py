"""
Proveedor de LLM para la aplicación.

Este módulo gestiona la inicialización del modelo de lenguaje (LLM)
utilizando la configuración definida en `src/config.py`.
"""
import logging
from langchain_openai import ChatOpenAI
from langchain_ollama.llms import OllamaLLM
from src.config import settings

def get_llm():
    """
    Retorna una instancia del LLM configurado según las variables de entorno
    gestionadas por el objeto `settings` de Pydantic.
    """
    provider = settings.LLM_PROVIDER.lower()
    logging.info(f"Seleccionando proveedor de LLM: {provider}")

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY no está configurada en .env. Por favor, añádela.")
        logging.info(f"Inicializando LLM OpenAI con el modelo '{settings.OPENAI_MODEL_NAME}'")
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL_NAME,
            temperature=settings.TEMPERATURE
        )
    elif provider == "local":
        if not settings.OLLAMA_BASE_URL or not settings.OLLAMA_MODEL:
            raise ValueError("Las variables OLLAMA_BASE_URL y OLLAMA_MODEL son requeridas para el proveedor local.")
        logging.info(f"Inicializando LLM local (Ollama) con el modelo '{settings.OLLAMA_MODEL}' en '{settings.OLLAMA_BASE_URL}'")
        return OllamaLLM(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=settings.TEMPERATURE
        )
    else:
        raise ValueError(f"Proveedor de LLM no soportado: {provider}")