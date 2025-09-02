"""
Tests de integración para la capa de servicio.
"""

import pytest
from unittest.mock import patch, MagicMock
from api.services.crew_service import run_analysis_crew
from src.models import SecurityReportInput
from src.logging_config import setup_agent_trace_logging  # Importar la función real


@patch("api.services.crew_service.run_mcp_analysis")
@patch(
    "api.services.crew_service.setup_agent_trace_logging"
)  # Mockear la configuración del logger
async def test_run_analysis_crew_success(mock_setup_logger, mock_run_mcp):
    """
    Test de integración para el servicio run_analysis_crew.
    Verifica que el servicio llama al orquestador MCP y devuelve el resultado.
    """
    # 1. Configuración del mock
    mock_run_mcp.return_value = '{"report_id": "service-test-123"}'

    # Configurar el mock del logger para que devuelva una instancia consistente
    mock_logger_instance = MagicMock()  # Una instancia de MagicMock para el logger
    mock_setup_logger.return_value = mock_logger_instance

    # 2. Llamada al servicio
    user_input = SecurityReportInput(text="Input de prueba para el servicio.")
    result = await run_analysis_crew(user_input)

    # 3. Aserciones
    mock_run_mcp.assert_called_once_with(
        "Input de prueba para el servicio.", mock_logger_instance
    )
    assert result == '{"report_id": "service-test-123"}'


@patch("api.services.crew_service.run_mcp_analysis")
@patch(
    "api.services.crew_service.setup_agent_trace_logging"
)  # Mockear la configuración del logger
async def test_run_analysis_crew_exception(mock_setup_logger, mock_run_mcp):
    """
    Verifica que el servicio propaga las excepciones del orquestador.
    """
    # 1. Configuración del mock para que lance un error
    mock_run_mcp.side_effect = Exception("Error en el orquestador")

    # Configurar el mock del logger para que devuelva una instancia consistente
    mock_logger_instance = MagicMock()  # Una instancia de MagicMock para el logger
    mock_setup_logger.return_value = mock_logger_instance

    # 2. Llamada al servicio y aserción de la excepción
    user_input = SecurityReportInput(text="Input que causa error.")
    with pytest.raises(Exception) as excinfo:
        await run_analysis_crew(user_input)

    # 3. Aserciones
    mock_run_mcp.assert_called_once_with("Input que causa error.", mock_logger_instance)
    assert "Error en el orquestador" in str(excinfo.value)
