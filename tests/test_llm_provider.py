"""
Tests para el proveedor de LLM.
"""

import pytest
from unittest.mock import patch, MagicMock
from langchain_openai import ChatOpenAI
from langchain_ollama.llms import OllamaLLM
from src.llm_provider import get_llm
from src.config import Settings


def test_get_llm_provider_openai(mocker):
    """Verifica que get_llm() devuelve una instancia de ChatOpenAI cuando LLM_PROVIDER es 'openai'."""
    # 1. Configurar un mock del objeto Settings
    mock_settings = Settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="test_openai_key",
        OPENAI_MODEL_NAME="gpt-4.1-nano",
        TEMPERATURE=0.5,
    )
    mocker.patch("src.llm_provider.settings", mock_settings)

    # 2. Mockear la clase ChatOpenAI para verificar su instanciación
    mock_chat_openai = mocker.patch("src.llm_provider.ChatOpenAI")

    # 3. Llamar a la función
    llm_instance = get_llm()

    # 4. Aserciones
    assert llm_instance == mock_chat_openai.return_value
    mock_chat_openai.assert_called_once_with(
        api_key="test_openai_key", model="gpt-4.1-nano", temperature=0.5
    )


def test_get_llm_provider_local_ollama(mocker):
    """
    Verifica que get_llm() devuelve una instancia de OllamaLLM cuando LLM_PROVIDER es 'local'.
    """
    mock_settings = Settings(
        LLM_PROVIDER="local",
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="llama3",
        TEMPERATURE=0.5,
        OPENAI_API_KEY="dummy_key",  # Pydantic requiere que los campos no opcionales existan
    )
    mocker.patch("src.llm_provider.settings", mock_settings)
    mock_ollama = mocker.patch("src.llm_provider.OllamaLLM")

    llm_instance = get_llm()

    assert llm_instance == mock_ollama.return_value
    mock_ollama.assert_called_once_with(
        base_url="http://localhost:11434", model="llama3", temperature=0.5
    )


def test_get_llm_provider_unsupported(mocker):
    """
    Verifica que se lanza un ValueError si el proveedor no es soportado.
    """
    mock_settings = Settings(
        LLM_PROVIDER="unsupported_provider", OPENAI_API_KEY="dummy_key"
    )
    mocker.patch("src.llm_provider.settings", mock_settings)

    with pytest.raises(ValueError) as excinfo:
        get_llm()

    assert "Proveedor de LLM no soportado: unsupported_provider" in str(excinfo.value)
