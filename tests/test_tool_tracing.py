import logging
from unittest.mock import patch
from src.trace import set_trace_logger
from src.tools.dbir_rag_tool import _dbir_rag_tool


def test_tool_tracing_logs(caplog):
    class DummyLogger(logging.Logger):
        pass

    logger = logging.getLogger("agent_trace_test")
    set_trace_logger(logger)

    with patch("src.tools.retriever.query_dbir_report", return_value="OK"):
        with caplog.at_level(logging.INFO):
            out = _dbir_rag_tool("test question")
            assert out == "OK"
            # Verificar que alguna de las etiquetas se logueó
            assert any("tool_invocation" in r.getMessage() or "tool_result" in r.getMessage() for r in caplog.records)

    # Limpiar
    set_trace_logger(None)

