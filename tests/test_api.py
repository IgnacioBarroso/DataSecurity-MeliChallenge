"""
Tests para el endpoint de la API /api/analyze.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app
import json

# Usar el cliente de prueba de FastAPI
client = TestClient(app)

@pytest.fixture
def mock_crew_service(mocker):
    """Mockea la capa de servicio para aislar el test del router."""
    # El servicio ahora es una corutina (async)
    return mocker.patch('api.routers.analysis.crew_service.run_analysis_crew')

def test_analyze_endpoint_success(mock_crew_service):
    """
    Test del "Happy Path" para el endpoint /analyze.
    Verifica que el router llama al servicio y devuelve una respuesta 200 OK con el JSON correcto.
    """
    # 1. Configuración del Mock
    # El servicio devuelve un string JSON, que es el resultado final del crew.
    mock_result_json_str = json.dumps({
        "report_id": "api-test-success-123",
        "summary": "Reporte generado exitosamente desde el mock del servicio."
    })
    mock_crew_service.return_value = mock_result_json_str

    # 2. Petición a la API
    response = client.post("/api/analyze", json={"user_input_text": "Describo mi app."})

    # 3. Aserciones
    assert response.status_code == 200
    mock_crew_service.assert_awaited_once() # Verificar que la corutina fue esperada (awaited)
    
    response_json = response.json()
    assert response_json["report_id"] == "api-test-success-123"
    assert response_json["summary"] == "Reporte generado exitosamente desde el mock del servicio."

def test_analyze_endpoint_service_error(mock_crew_service):
    """
    Test del "Sad Path" para el endpoint /analyze.
    Verifica que el router maneja excepciones del servicio y devuelve un error 500.
    """
    # 1. Configuración del Mock para que lance una excepción
    mock_crew_service.side_effect = Exception("Error simulado y crítico en el crew")

    # 2. Petición a la API
    response = client.post("/api/analyze", json={"user_input_text": "Input que causa error."})

    # 3. Aserciones
    assert response.status_code == 500
    assert "error interno inesperado" in response.json()["detail"]

def test_analyze_endpoint_invalid_input(mock_crew_service):
    """
    Test para un input inválido (ej. texto vacío) que debería ser manejado por el servicio.
    Verifica que se devuelve un error 422 Unprocessable Entity.
    """
    # 1. Configuración del Mock para que lance un ValueError (input inválido)
    mock_crew_service.side_effect = ValueError("El input del usuario no puede estar vacío.")

    # 2. Petición a la API
    response = client.post("/api/analyze", json={"user_input_text": ""})

    # 3. Aserciones
    assert response.status_code == 422
    assert "El input del usuario no puede estar vacío." in response.json()["detail"]
