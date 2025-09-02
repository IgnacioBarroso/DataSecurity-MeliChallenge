"""
Test para el orquestador MCP y el flujo entre crews.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.models import EcosystemContext, AnalyzedThreats, ClassifiedThreats, FinalSecurityReport, ThreatVector, ClassifiedThreat, MitreTechnique, ActionableRecommendation
import logging

@pytest.fixture
def mock_crew_outputs():
    """Prepara los objetos Pydantic que simulan la salida de cada sub-crew."""
    # Salida de la primera crew (threat_intel)
    analyzed_threats = AnalyzedThreats(
        threats=[ThreatVector(threat_vector="Phishing", justification="Justificación de Phishing.")]
    )
    # Salida de la segunda crew (mitre_classification)
    classified_threats = ClassifiedThreats(
        classified_threats=[ClassifiedThreat(
            threat_vector="Phishing", 
            justification="Justificación de Phishing.",
            mitre_techniques=[MitreTechnique(id="T1566", name="Phishing", description="...")],
            risk_level="Alto",
            risk_rationale="Riesgo alto por posible robo de credenciales."
        )]
    )
    # Salida de la tercera crew (reporting)
    final_report = FinalSecurityReport(
        report_id="mock-report-123",
        application_name="App Mockeada",
        summary="Resumen del reporte mockeado.",
        prioritized_detectors=[
            ActionableRecommendation(
                priority=1, detector_name="Detector de Phishing", risk_level="Alto",
                threat_vector="Phishing", mitre_techniques=[],
                rationale="...", actionable_steps=[]
            )
        ]
    )
    return [analyzed_threats, classified_threats, final_report]

def test_mcp_orchestration_flow(mocker, mock_crew_outputs):
    """
    Testea el flujo de orquestación en `run_mcp_analysis`.
    Verifica que el output de una crew se pasa correctamente a la siguiente.
    """
    # 1. Preparar los mocks de las sub-crews
    mock_threat_intel_crew = MagicMock()
    mock_mitre_crew = MagicMock()
    mock_reporting_crew = MagicMock()

    # 2. Configurar el valor de retorno de kickoff() para cada mock
    mock_threat_intel_crew.kickoff.return_value = mock_crew_outputs[0]
    mock_mitre_crew.kickoff.return_value = mock_crew_outputs[1]
    mock_reporting_crew.kickoff.return_value = mock_crew_outputs[2]

    # 3. Mockear las funciones que crean las crews para que devuelvan nuestros mocks
    mocker.patch('src.mcp_crews.create_threat_intel_crew', return_value=mock_threat_intel_crew)
    mocker.patch('src.mcp_crews.create_mitre_classification_crew', return_value=mock_mitre_crew)
    mocker.patch('src.mcp_crews.create_reporting_crew', return_value=mock_reporting_crew)

    # 4. Importar y ejecutar la función a probar
    from src.mcp_crews import run_mcp_analysis
    user_input = "Describo mi app para el test de orquestación."
    
    # Crear un logger mock para pasar a la función
    mock_logger = MagicMock(spec=logging.Logger)

    final_result_json = run_mcp_analysis(user_input, mock_logger)

    # 5. Aserciones
    # Verificar que cada crew fue llamada una vez
    mock_threat_intel_crew.kickoff.assert_called_once()
    mock_mitre_crew.kickoff.assert_called_once()
    mock_reporting_crew.kickoff.assert_called_once()

    # Verificar que el input de la segunda crew es el output de la primera
    mitre_input = mock_mitre_crew.kickoff.call_args[1]['inputs']
    assert mitre_input['threats'][0]['threat_vector'] == "Phishing"

    # Verificar que el input de la tercera crew es el output de la segunda
    reporting_input = mock_reporting_crew.kickoff.call_args[1]['inputs']
    assert reporting_input['classified_threats'][0]['risk_level'] == "Alto"

    # Verificar que el resultado final es el JSON del reporte de la última crew
    import json
    final_result = json.loads(final_result_json)
    assert final_result['report_id'] == "mock-report-123"
    assert final_result['summary'] == "Resumen del reporte mockeado."
