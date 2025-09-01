def test_dbir_rag_tool_logs_error_on_exception(mocker, caplog):
    """
    Verifica que DBIRReportQueryTool loguea un error si query_dbir_report lanza una excepción.
    """
    # Mockea _initialize_retriever para que lance una excepción y así forzar el flujo real de logging
    mocker.patch("src.tools.dbir_rag_tool._initialize_retriever", side_effect=Exception("Simulated initialization failure"))
    from src.tools.dbir_rag_tool import DBIRReportQueryTool
    with caplog.at_level("ERROR"):
        result = DBIRReportQueryTool()._run("consulta de prueba")
    assert "error" in caplog.text.lower()
    assert "dbir" in caplog.text.lower()
    assert "simulated initialization failure" in caplog.text.lower()
    assert "error" in result.lower()
    assert "An error occurred while retrieving information from the DBIR report." in result
import pytest
from api.services.crew_service import run_security_analysis
from src.tools.dbir_rag_tool import dbir_rag_tool
from src.tools.mitre_tool import mitre_attack_query_tool

# ===================== TESTS DE SEGURIDAD Y LOGS =====================

def test_no_sensitive_data_in_logs_on_invalid_input(caplog):
    """
    Verifica que los logs no contienen información sensible al recibir input inválido.
    """
    print("[TEST LOG] Checking logs for invalid input...")
    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError):
            run_security_analysis("")
    for record in caplog.records:
        assert "GEMINI_API_KEY" not in record.getMessage()
        assert "token" not in record.getMessage().lower()
        assert "password" not in record.getMessage().lower()

import pytest

@pytest.mark.parametrize("tool_name,query", [
    ("dbir", "vector de amenaza inexistente"),
    ("mitre", "técnica mitre inexistente"),
])
def test_error_logging_on_tool_failure(tool_name, query, mocker, caplog):
    """
    Verifica que se loguea un error cuando una herramienta falla y que el log es claro.
    """
    if tool_name == "dbir":
        mocker.patch("src.tools.dbir_rag_tool._initialize_retriever", side_effect=Exception("Simulated initialization failure"))
        from src.tools.dbir_rag_tool import DBIRReportQueryTool
        tool_func = DBIRReportQueryTool()._run
    else:
        from src.tools.mitre_tool import mitre_attack_query_tool
        tool_func = mitre_attack_query_tool.run
    print(f"[TEST LOG] Checking error logs in tool: {tool_func.__name__}")
    with caplog.at_level("ERROR"):
        tool_func(query)
    assert any("error" in record.getMessage().lower() for record in caplog.records)
    # No debe haber datos sensibles
    for record in caplog.records:
        assert "GEMINI_API_KEY" not in record.getMessage()
        assert "token" not in record.getMessage().lower()
        assert "password" not in record.getMessage().lower()
