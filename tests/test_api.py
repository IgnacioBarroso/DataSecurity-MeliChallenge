"""
Tests para el endpoint de la API /api/analyze.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

# Usar el cliente de prueba de FastAPI
client = TestClient(app)


@pytest.fixture
def mock_crew_service(mocker):
    """Mockea la capa de servicio para aislar el test del router."""
    # El servicio ahora es una corutina (async)
    return mocker.patch("api.routers.analysis.crew_service.run_analysis_crew")


def test_analyze_endpoint_success(mock_crew_service):
    """
    Test del "Happy Path" para el endpoint /analyze.
    Verifica que el router llama al servicio y devuelve una respuesta 200 OK con el JSON correcto.
    """
    # 1. Configuración del Mock
    # El servicio debe devolver un dict con las claves correctas para AnalysisResponse
    mock_result_dict = {
        "report_json": "{\"ok\": true}",
        "session_id": "api-test-success-123",
    }
    mock_crew_service.return_value = mock_result_dict

    # 2. Petición a la API
    response = client.post("/api/analyze", json={"user_input": "Describo mi app."})

    # 3. Aserciones
    assert response.status_code == 200
    mock_crew_service.assert_awaited_once()  # Verificar que la corutina fue esperada (awaited)

    response_json = response.json()
    assert response_json["session_id"] == "api-test-success-123"
    assert response_json["report_json"] == "{\"ok\": true}"


def test_analyze_endpoint_service_error(mock_crew_service):
    """
    Test del "Sad Path" para el endpoint /analyze.
    Verifica que el router maneja excepciones del servicio y devuelve un error 500.
    """
    # 1. Configuración del Mock para que lance una excepción
    mock_crew_service.side_effect = Exception("Error simulado y crítico en el crew")

    # 2. Petición a la API
    response = client.post(
        "/api/analyze", json={"user_input": "Input que causa error."}
    )

    # 3. Aserciones
    assert response.status_code == 500
    assert "error interno inesperado" in response.json()["detail"]


def test_analyze_endpoint_invalid_input(mock_crew_service):
    """
    Test para un input inválido (ej. texto vacío) que debería ser manejado por el servicio.
    Verifica que se devuelve un error 422 Unprocessable Entity.
    """
    # 1. Configuración del Mock para que lance un ValueError (input inválido)
    mock_crew_service.side_effect = ValueError(
        "El input del usuario no puede estar vacío."
    )

    # 2. Petición a la API
    response = client.post("/api/analyze", json={"user_input": ""})

    # 3. Aserciones
    assert response.status_code == 422
    assert "El input del usuario no puede estar vacío." in response.json()["detail"]
