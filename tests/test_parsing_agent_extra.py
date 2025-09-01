import pytest
from api.services.crew_service import run_security_analysis

# ===================== TESTS DE ERRORES Y CASOS LÍMITE =====================

@pytest.mark.parametrize("user_input_text", [
    "",
    None,
    "   ",
])
def test_input_parsing_agent_invalid_inputs(user_input_text):
    """
    Test de error: verifica el comportamiento ante entradas inválidas o vacías.
    """
    print("\033[91m[TEST ERROR] Probando entrada inválida para InputParsingAgent:\033[0m", repr(user_input_text))
    with pytest.raises(ValueError) as excinfo:
        run_security_analysis(user_input_text)
    assert "no puede estar vacío" in str(excinfo.value)
