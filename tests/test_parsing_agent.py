"""
Test para el agente de parseo de input.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.mcp_crews import parsing_agent  # Importar la instancia del agente
from src.models import EcosystemContext
from crewai import Task, Crew, Process

@pytest.fixture
def mock_llm_for_parsing(mocker):
    """Mockea la respuesta del LLM para el agente de parseo."""
    # El LLM debe devolver un string JSON que se pueda parsear a EcosystemContext
    output_json = EcosystemContext(
        application_name="App de Prueba de Parseo",
        usage_description="Descripción de uso para el test.",
        exposed_apis=["api/v1/users", "api/v1/products"],
        technologies=["Python", "Django", "React"],
        current_controls=["Autenticación MFA", "WAF"]
    ).model_dump_json()

    # Mockeamos la función `call` del LLM que usa el agente
    # parsing_agent.llm es la instancia de CrewAI LLM, que tiene un método `call`
    mocker.patch.object(parsing_agent.llm, 'call', return_value=output_json)

def test_input_parsing_agent_task(mock_llm_for_parsing):
    """
    Verifica que la tarea del agente de parseo procesa correctamente el texto
    y devuelve un objeto EcosystemContext válido.
    """
    # 1. Crear la tarea para el agente
    parsing_task = Task(
        description="Analiza el siguiente texto: 'Mi app se llama App de Prueba de Parseo...'",
        expected_output="Un objeto JSON que cumpla con el modelo Pydantic EcosystemContext.",
        agent=parsing_agent,
        output_pydantic=EcosystemContext
    )

    # 2. Crear una crew temporal para ejecutar la tarea
    crew = Crew(
        agents=[parsing_agent],
        tasks=[parsing_task],
        process=Process.sequential,
        verbose=False
    )

    # 3. Ejecutar la crew
    result = crew.kickoff()

    # 4. Aserciones
    # El resultado de kickoff con `output_pydantic` es un CrewOutput, el modelo Pydantic está en .pydantic
    assert isinstance(result.pydantic, EcosystemContext), "El resultado debe ser una instancia de EcosystemContext"
    assert result.pydantic.application_name == "App de Prueba de Parseo"
    assert "Python" in result.pydantic.technologies
    assert "api/v1/users" in result.pydantic.exposed_apis
    assert "Autenticación MFA" in result.pydantic.current_controls
