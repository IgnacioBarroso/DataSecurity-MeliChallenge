from unittest.mock import patch
from fastapi.testclient import TestClient
from src.models import FinalSecurityReport, ActionableRecommendation, MitreTechnique
from api.main import app

# Cliente de prueba para la aplicación FastAPI
client = TestClient(app)


@patch('api.routers.analysis.crew_service.run_security_analysis')
def test_analyze_endpoint_success(mock_run_analysis):
    """
    Test del "Happy Path" para el endpoint /analyze.
    Mockea la capa de servicio para asegurar que el endpoint responde correctamente
    cuando el servicio funciona como se espera.
    """
    # 1. Configuración del Mock
    # Se crea un reporte de ejemplo que el servicio mockeado devolverá.
    mock_report = FinalSecurityReport(
        report_id="test-success-123",
        application_name="App de Prueba Exitosa",
        summary="Reporte generado exitosamente por el mock.",
        prioritized_detectors=[
            ActionableRecommendation(
                priority=1, detector_name="Detector Mock", risk_level="Crítico",
                threat_vector="Vector Mock", mitre_techniques=[],
                rationale="Test de éxito", actionable_steps=[]
            )
        ]
    )
    mock_run_analysis.return_value = mock_report

    # 2. Petición a la API
    # Se envía una solicitud POST al endpoint.
    response = client.post("/api/analyze", json={"user_input_text": "Describo mi app."})

    # 3. Aserciones (Verificaciones)
    # Se verifica que el servicio fue llamado, que la respuesta es 200 OK,
    # y que el cuerpo de la respuesta es el esperado.
    mock_run_analysis.assert_called_once()
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["report_id"] == "test-success-123"
    assert response_json["summary"] == "Reporte generado exitosamente por el mock."


@patch('api.routers.analysis.crew_service.run_security_analysis')
def test_analyze_endpoint_service_error(mock_run_analysis):
    """
    Test del "Sad Path" para el endpoint /analyze.
    Verifica que el endpoint maneja correctamente las excepciones que ocurren
    en la capa de servicio y devuelve un error 500.
    """
    # 1. Configuración del Mock
    # Se configura el mock para que lance una excepción cuando sea llamado.
    mock_run_analysis.side_effect = ValueError("Error simulado en el crew")

    # 2. Petición a la API
    response = client.post("/api/analyze", json={"user_input_text": "Input que causa error."})

    # 3. Aserciones
    # Se verifica que el código de estado es 500 y que el mensaje de error es el esperado.
    assert response.status_code == 422
    assert response.json() == {"detail": "Error simulado en el crew"}