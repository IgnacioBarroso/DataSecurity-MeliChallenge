import pytest
from unittest.mock import patch
from api.services.crew_service import run_analysis_crew  # Importar la función correcta
from src.models import SecurityReportInput  # Importar SecurityReportInput

# ===================== TESTS DE SEGURIDAD Y LOGS =====================


@pytest.mark.asyncio  # Marcar el test como asíncrono
@patch(
    "api.services.crew_service.run_mcp_analysis"
)  # Mockear la ejecución del crew completo
async def test_no_sensitive_data_in_logs_on_invalid_input(mock_run_mcp, caplog):
    """
    Verifica que los logs no contienen información sensible al recibir input inválido.
    """
    # Configurar el mock para que el orquestador lance un ValueError si el input es vacío
    mock_run_mcp.side_effect = ValueError("El input del usuario no puede estar vacío.")

    print("[TEST LOG] Checking logs for invalid input...")
    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError):
            await run_analysis_crew(SecurityReportInput(text=""))  # Llamada asíncrona
    for record in caplog.records:
        assert "OPENAI_API_KEY" not in record.getMessage()  # Cambiar a OPENAI_API_KEY
        assert "token" not in record.getMessage().lower()
        assert "password" not in record.getMessage().lower()

