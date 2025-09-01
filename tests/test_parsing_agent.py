
import pytest
from unittest.mock import MagicMock
from src.agents import InputParsingAgent
from src.models import EcosystemContext
from crewai import Task

@pytest.fixture
def mock_llm_for_parsing_agent(mocker):
    """Mockea el LLM para simular la respuesta del InputParsingAgent."""
    mock_llm_instance = mocker.patch('src.agents.llm')
    # Simula que el LLM devuelve un JSON válido que se mapea a EcosystemContext
    mock_llm_instance.invoke.return_value = EcosystemContext(
        application_name="App de Prueba de Parseo",
        usage_description="Descripción de uso para el test.",
        exposed_apis=["api/v1/users", "api/v1/products"],
        technologies=["Python", "Django", "React"],
        current_controls=["Autenticación MFA", "WAF"]
    )
    return mock_llm_instance

def test_input_parsing_agent_task(mock_llm_for_parsing_agent):
    """
    Verifica que el InputParsingAgent, a través de su tarea, puede procesar un texto
    y devolver un objeto EcosystemContext válido.
    """
    # Crear una instancia de la tarea de parseo
    parsing_task = Task(
        description="Analiza el siguiente texto proporcionado por el usuario: 'Mi app se llama App de Prueba de Parseo, es para usuarios y productos, usa Python, Django y React, y tiene MFA y WAF.'. Extrae la información clave y formatéala estrictamente como un objeto Pydantic 'EcosystemContext'. Tu única salida debe ser este objeto Pydantic.",
        expected_output="Una única instancia del modelo Pydantic 'EcosystemContext' rellenada con la información extraída del texto de entrada.",
        agent=InputParsingAgent,
        output_pydantic=EcosystemContext
    )

    # Ejecutar la tarea (esto internamente llamará al agente y al LLM mockeado)
    # CrewAI Task.execute() espera un contexto, pero para la primera tarea, puede ser vacío o con user_input_text
    # Aquí simulamos el input que CrewAI pasaría a la tarea
    task_output = parsing_task.execute(context={'user_input_text': "Mi app se llama App de Prueba de Parseo, es para usuarios y productos, usa Python, Django y React, y tiene MFA y WAF.", 'session_id': 'test-session-id'})

    # Aserciones
    assert isinstance(task_output, EcosystemContext)
    assert task_output.application_name == "App de Prueba de Parseo"
    assert "Python" in task_output.technologies
    assert "api/v1/users" in task_output.exposed_apis
    assert "Autenticación MFA" in task_output.current_controls

    # Verificar que el LLM fue invocado
    mock_llm_for_parsing_agent.invoke.assert_called_once()
