"""
Configuración centralizada de la aplicación utilizando Pydantic Settings.

Este módulo carga la configuración desde variables de entorno y/o un archivo .env,
proporcionando un objeto `settings` único, validado y con tipado estático para toda la aplicación.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Modo del analizador: "heavy" (por defecto) o "turbo"
    ANALYZER_MODE: str = "heavy"
    # Configuración MCP externo
    MCP_EXTERNAL_HOST: str = "mitre-mcp"
    MCP_EXTERNAL_PORT: int = 8080
    MCP_EXTERNAL_PROTOCOL: str = "http"
    # Configuración de ChromaDB remoto (por defecto usa el servicio docker 'chromadb')
    CHROMA_DB_HOST: str | None = "chromadb"
    CHROMA_DB_PORT: int | None = 8000
    """
    Define las variables de configuración de la aplicación.

    Pydantic leerá automáticamente estas variables desde el entorno o un archivo .env.
    """

    # Configuración del modelo de lenguaje
    LLM_PROVIDER: str = "openai"
    TEMPERATURE: float = 0.1

    # Configuración de OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str = "gpt-4.1-nano"

    # Configuración de Cohere (opcional para re-ranking)
    COHERE_API_KEY: str | None = None

    # Configuración de Ollama (opcional, para futura referencia)
    OLLAMA_BASE_URL: str | None = None
    OLLAMA_MODEL: str | None = None

    # Configuración del sistema RAG
    CHROMA_DB_PATH: str = "vector_db"
    COLLECTION_NAME: str = "dbir_2025"

    # Redis Docstore (opcional)
    REDIS_HOST: str | None = None
    REDIS_PORT: int | None = None
    REDIS_DB: int = 0

    # Cargar desde el archivo .env en la raíz del proyecto
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Helpers
    @property
    def is_turbo(self) -> bool:
        return (self.ANALYZER_MODE or "").lower().strip() == "turbo"


# Crear una única instancia de la configuración para ser importada en otros módulos
settings = Settings()
