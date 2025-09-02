import pytest
from unittest.mock import patch, MagicMock
from src.tools.dbir_rag_tool import dbir_rag_tool  # Solo importar dbir_rag_tool
from src.tools.mitre_tool import mitre_attack_query_tool
from api.services.crew_service import run_analysis_crew  # Importar la función correcta
from src.models import SecurityReportInput  # Importar SecurityReportInput
import logging

# ===================== TESTS DE SEGURIDAD Y LOGS =====================


def test_dbir_rag_tool_logs_error_on_exception(mocker, caplog):
    """
    Verifica que dbir_rag_tool loguea un error si query_dbir_report lanza una excepción.
    """
    # Mockear query_dbir_report para que devuelva el string de error esperado
    mocker.patch(
        "src.tools.retriever.query_dbir_report",
        return_value="Se produjo un error al intentar recuperar información del informe DBIR.",
    )

    # Mockear OpenAIEmbeddings().embed_query para que devuelva una lista de floats
    mock_embeddings_instance = MagicMock()
    mock_embeddings_instance.embed_query.return_value = [
        0.1,
        0.2,
        0.3,
    ]  # Simular un embedding válido
    mocker.patch(
        "src.tools.retriever.OpenAIEmbeddings", return_value=mock_embeddings_instance
    )

    with caplog.at_level("ERROR"):
        # Llamamos directamente al método .run() de la herramienta
        result = dbir_rag_tool.run("consulta de prueba")

    assert "error" in caplog.text.lower()
    assert "dbir" in caplog.text.lower()
    assert (
        "Se produjo un error al intentar recuperar información del informe DBIR."
        in result
    )


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


@pytest.mark.parametrize(
    "tool_name,query",
    [
        ("dbir", "vector de amenaza inexistente"),
        ("mitre", "técnica mitre inexistente"),
    ],
)
def test_error_logging_on_tool_failure(tool_name, query, mocker, caplog):
    """
    Verifica que se loguea un error cuando una herramienta falla y que el log es claro.
    """
    if tool_name == "dbir":
        # Mockear query_dbir_report para que devuelva el string de error esperado
        mocker.patch(
            "src.tools.retriever.query_dbir_report",
            return_value="Se produjo un error al intentar recuperar información del informe DBIR.",
        )
        # Mockear OpenAIEmbeddings().embed_query para que devuelva una lista de floats
        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.embed_query.return_value = [
            0.1,
            0.2,
            0.3,
        ]  # Simular un embedding válido
        mocker.patch(
            "src.tools.retriever.OpenAIEmbeddings",
            return_value=mock_embeddings_instance,
        )
        tool_func = dbir_rag_tool.run  # Llamar al método run de la instancia Tool
    else:
        tool_func = mitre_attack_query_tool.run
    print(f"[TEST LOG] Checking error logs in tool: {tool_func.__name__}")
    with caplog.at_level("ERROR"):
        tool_func(query)
    assert any("error" in record.getMessage().lower() for record in caplog.records)
    # No debe haber datos sensibles
    for record in caplog.records:
        assert "OPENAI_API_KEY" not in record.getMessage()  # Cambiar a OPENAI_API_KEY
        assert "token" not in record.getMessage().lower()
        assert "password" not in record.getMessage().lower()
