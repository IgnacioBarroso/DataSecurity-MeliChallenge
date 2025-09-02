"""
Configuración centralizada de la aplicación utilizando Pydantic Settings.

Este módulo carga la configuración desde variables de entorno y/o un archivo .env,
proporcionando un objeto `settings` único, validado y con tipado estático para toda la aplicación.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Define las variables de configuración de la aplicación.

    Pydantic leerá automáticamente estas variables desde el entorno o un archivo .env.
    """

    # Configuración del modelo de lenguaje
    LLM_PROVIDER: str = "openai"
    TEMPERATURE: float = 0.1

    # Configuración de OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str = "gpt-4.1-2025-04-14"

    # Configuración de Ollama (opcional, para futura referencia)
    OLLAMA_BASE_URL: str | None = None
    OLLAMA_MODEL: str | None = None

    # Configuración del sistema RAG
    CHROMA_DB_PATH: str = "vector_db"
    COLLECTION_NAME: str = "dbir_2025"

    # Cargar desde el archivo .env en la raíz del proyecto
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Crear una única instancia de la configuración para ser importada en otros módulos
settings = Settings()
