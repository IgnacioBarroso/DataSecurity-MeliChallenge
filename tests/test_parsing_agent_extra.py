"""
Tests para casos límite y errores relacionados con el input del agente de parseo.
"""
import pytest
from unittest.mock import patch, MagicMock
from api.services.crew_service import run_analysis_crew
from src.models import SecurityReportInput
from src.logging_config import setup_agent_trace_logging # Importar la función real

# ===================== TESTS DE ERRORES Y CASOS LÍMITE =====================

@pytest.mark.parametrize("user_input_text", [
    "",
    "   ",
])
@patch('api.services.crew_service.run_mcp_analysis') # Mockear la ejecución del crew completo
@patch('api.services.crew_service.setup_agent_trace_logging') # Mockear la configuración del logger
async def test_input_parsing_agent_invalid_inputs(mock_setup_logger, mock_run_mcp, user_input_text):
    """
    Test de error: verifica el comportamiento ante entradas inválidas o vacías.
    El servicio debe lanzar un ValueError si el input es inválido.
    """
    # Configurar el mock para que el orquestador lance un ValueError si el input es vacío
    # Esto simula el comportamiento esperado del parsing_agent si recibe un input vacío
    if not user_input_text.strip():
        mock_run_mcp.side_effect = ValueError("El input del usuario no puede estar vacío.")
    
    # Configurar el mock del logger para que devuelva una instancia consistente
    mock_logger_instance = MagicMock() # Una instancia de MagicMock para el logger
    mock_setup_logger.return_value = mock_logger_instance

    # Crear el objeto SecurityReportInput
    report_input = SecurityReportInput(text=user_input_text)

    with pytest.raises(ValueError) as excinfo:
        await run_analysis_crew(report_input)
    
    assert "no puede estar vacío" in str(excinfo.value)

    # Verificar que run_mcp_analysis fue llamado con el input correcto y el logger mockeado
    mock_run_mcp.assert_called_once_with(user_input_text, mock_logger_instance)