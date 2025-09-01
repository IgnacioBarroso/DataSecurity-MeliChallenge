
import pytest
from unittest.mock import patch, MagicMock

# Importar las clases de LLM que esperamos instanciar
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama

# Importar la función a probar
from src.llm_provider import get_llm

# Mockear la variable GEMINI_API_KEY para evitar errores de configuración real
@pytest.fixture(autouse=True)
def mock_gemini_api_key_env(mocker):
    mocker.patch('src.config.GEMINI_API_KEY', 'mock_gemini_key')


def test_get_llm_provider_google(mocker):
    """Verifica que get_llm() devuelve una instancia de ChatGoogleGenerativeAI cuando LLM_PROVIDER es 'google'."""
    # Mockear os.getenv para simular las variables de entorno
    mocker.patch('os.getenv', side_effect=lambda key, default=None: {
        "LLM_PROVIDER": "google",
        "GEMINI_API_KEY": "test_google_key"
    }.get(key, default))

    # Mockear la clase ChatGoogleGenerativeAI para evitar la instanciación real
    mock_chat_google_generative_ai = mocker.patch('langchain_google_genai.ChatGoogleGenerativeAI')

    llm_instance = get_llm()

    # Aserciones
    assert isinstance(llm_instance, MagicMock) # Es un mock, no la clase real
    mock_chat_google_generative_ai.assert_called_once_with(
        model="gemini-1.5-pro-latest",
        verbose=True,
        temperature=0.1,
        google_api_key="test_google_key"
    )


def test_get_llm_provider_local(mocker):
    """Verifica que get_llm() devuelve una instancia de Ollama cuando LLM_PROVIDER es 'local'."""
    # Mockear os.getenv
    mocker.patch('os.getenv', side_effect=lambda key, default=None: {
        "LLM_PROVIDER": "local",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "llama3"
    }.get(key, default))

    # Mockear la clase Ollama
    mock_ollama = mocker.patch('langchain_community.llms.Ollama')

    llm_instance = get_llm()

    # Aserciones
    assert isinstance(llm_instance, MagicMock) # Es un mock
    mock_ollama.assert_called_once_with(
        base_url="http://localhost:11434",
        model="llama3"
    )


def test_get_llm_fallback_to_google_on_local_error(mocker):
    """Verifica que get_llm() hace fallback a Google si la configuración local de Ollama falla."""
    # Mockear os.getenv para simular configuración local incompleta
    mocker.patch('os.getenv', side_effect=lambda key, default=None: {
        "LLM_PROVIDER": "local",
        "OLLAMA_BASE_URL": None, # Simula que falta la URL
        "OLLAMA_MODEL": "llama3",
        "GEMINI_API_KEY": "fallback_google_key"
    }.get(key, default))

    # Mockear las clases de LLM
    mock_ollama = mocker.patch('langchain_community.llms.Ollama')
    mock_chat_google_generative_ai = mocker.patch('langchain_google_genai.ChatGoogleGenerativeAI')

    llm_instance = get_llm()

    # Aserciones
    mock_ollama.assert_not_called() # Ollama no debería ser instanciado
    assert isinstance(llm_instance, MagicMock) # Es un mock
    mock_chat_google_generative_ai.assert_called_once_with(
        model="gemini-1.5-pro-latest",
        verbose=True,
        temperature=0.1,
        google_api_key="fallback_google_key"
    )


def test_get_llm_raises_error_if_google_key_missing(mocker):
    """Verifica que get_llm() lanza un ValueError si GEMINI_API_KEY falta para el proveedor 'google'."""
    # Mockear os.getenv para simular que falta la API key de Gemini
    mocker.patch('os.getenv', side_effect=lambda key, default=None: {
        "LLM_PROVIDER": "google",
        "GEMINI_API_KEY": None # Simula que falta la clave
    }.get(key, default))

    # Se espera que se lance un ValueError
    with pytest.raises(ValueError, match="GEMINI_API_KEY no está configurada."):
        get_llm()
