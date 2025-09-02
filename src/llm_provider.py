"""
Proveedor de LLM para la aplicación.

Este módulo gestiona la inicialización del modelo de lenguaje (LLM)
utilizando la configuración definida en `src/config.py`.
"""

import logging
import os  # Import os
from langchain_openai import ChatOpenAI
from langchain_ollama.llms import OllamaLLM
from src.config import settings


def get_llm():
    """
    Inicializa y retorna el LLM configurado según la variable LLM_PROVIDER.
    Soporta 'openai' (cloud) y 'ollama' (local, GPU).
    """
    provider = settings.LLM_PROVIDER.lower()
    logging.info(f"Seleccionando proveedor de LLM: {provider}")

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY no está configurada en .env. Por favor, añádela."
            )
        # Permitir que el modelo sea exactamente el que se pasa en settings (ej: gpt-4.1-nano)
        model_name = getattr(settings, "OPENAI_MODEL_NAME", "gpt-4.1-nano")
        logging.info(f"Inicializando LLM OpenAI con el modelo '{model_name}'")
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=model_name,
            temperature=settings.TEMPERATURE,
        )
    elif provider in ("ollama", "local"):
        if not settings.OLLAMA_BASE_URL or not settings.OLLAMA_MODEL:
            raise ValueError(
                "Las variables OLLAMA_BASE_URL y OLLAMA_MODEL son requeridas para el proveedor Ollama."
            )
        logging.info(
            f"Inicializando LLM Ollama con el modelo '{settings.OLLAMA_MODEL}' en '{settings.OLLAMA_BASE_URL}'"
        )
        return OllamaLLM(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=settings.TEMPERATURE,
        )
    else:
        raise ValueError(
            f"Proveedor de LLM no soportado: {provider}. Usa 'openai' o 'ollama'."
        )
