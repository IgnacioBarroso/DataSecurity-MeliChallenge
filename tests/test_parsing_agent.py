import pytest
from unittest.mock import MagicMock
from src.agents import InputParsingAgent
from src.models import EcosystemContext
from crewai import Task, Crew, Process

@pytest.fixture
def mock_llm_for_parsing_agent(mocker):
    """Mockea el LLM para simular la respuesta del InputParsingAgent."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = EcosystemContext(
        application_name="App de Prueba de Parseo",
        usage_description="Descripción de uso para el test.",
        exposed_apis=["api/v1/users", "api/v1/products"],
        technologies=["Python", "Django", "React"],
        current_controls=["Autenticación MFA", "WAF"]
    ).model_dump_json()
    # Simula la respuesta de litellm.completion como un objeto con .choices y .message.content
    mock_message = MagicMock()
    mock_message.content = mock_llm.invoke.return_value
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mocker.patch('litellm.completion', return_value=mock_response)
    return mock_llm

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

    # Crear un crew temporal para ejecutar la tarea
    crew = Crew(
        agents=[InputParsingAgent],
        tasks=[parsing_task],
        process=Process.sequential,
        verbose=False
    )

    # Ejecutar el crew
    task_output = crew.kickoff(inputs={'user_input_text': "Mi app se llama App de Prueba de Parseo, es para usuarios y productos, usa Python, Django y React, y tiene MFA y WAF.", 'session_id': 'test-session-id'})

    # Aserciones: CrewOutput contiene el modelo Pydantic en .pydantic
    assert hasattr(task_output, "pydantic"), "El resultado debe tener el atributo .pydantic"
    assert isinstance(task_output.pydantic, EcosystemContext), "El atributo .pydantic debe ser una instancia de EcosystemContext"
    assert task_output.pydantic.application_name == "App de Prueba de Parseo"
    assert "Python" in task_output.pydantic.technologies
    assert "api/v1/users" in task_output.pydantic.exposed_apis
    assert "Autenticación MFA" in task_output.pydantic.current_controls
    # ...no es necesario verificar el call_count del mock, ya que el agente usa el LLM global...
