import pytest
from unittest.mock import MagicMock
from src.main_crew import security_analysis_crew
from src.models import EcosystemContext, AnalyzedThreats, ClassifiedThreats, FinalSecurityReport, ThreatVector, ClassifiedThreat, MitreTechnique, ActionableRecommendation

@pytest.fixture
def mock_llm_pipeline_output():
    """Prepara una secuencia de salidas Pydantic simuladas para todo el pipeline del crew."""
    # 1. Salida del InputParsingAgent
    ecosystem_context = EcosystemContext(
        application_name="App de Test para Crew",
        usage_description="Una app de prueba.",
        exposed_apis=["/api/data"],
        technologies=["Python"],
        current_controls=["MFA"]
    )
    # 2. Salida del RAGThreatAnalyzerAgent
    analyzed_threats = AnalyzedThreats(threats=[ThreatVector(threat_vector="Ataques de Phishing", justification="El DBIR menciona el phishing como amenaza común.")])
    # 3. Salida del RAGQualityValidatorAgent (pasa los datos sin cambios)
    validated_threats = analyzed_threats
    # 4. Salida del TTPRiskClassifierAgent
    classified_threats = ClassifiedThreats(
        classified_threats=[
            ClassifiedThreat(
                threat_vector="Ataques de Phishing",
                justification="El DBIR menciona el phishing como amenaza común.",
                mitre_techniques=[MitreTechnique(id="T1566", name="Phishing", description="...")],
                risk_level="Alto",
                risk_rationale="El phishing puede llevar al robo de credenciales."
            )
        ]
    )
    # 5. Salida del ActionableReportingSpecialistAgent
    final_report = FinalSecurityReport(
        report_id="final-report-mock-id",
        application_name="App de Test para Crew",
        summary="Resumen del reporte final.",
        prioritized_detectors=[
            ActionableRecommendation(
                priority=1,
                detector_name="Detector de Phishing Avanzado",
                risk_level="Alto",
                threat_vector="Ataques de Phishing",
                mitre_techniques=[MitreTechnique(id="T1566", name="Phishing", description="...")],
                rationale="El phishing es un vector de entrada crítico.",
                actionable_steps=["Implementar filtros de email avanzados."]
            )
        ]
    )
    return [ecosystem_context.model_dump_json(), analyzed_threats.model_dump_json(), validated_threats.model_dump_json(), classified_threats.model_dump_json(), final_report.model_dump_json()]

def test_crew_full_integration_flow(mocker, mock_llm_pipeline_output):
    """
    Test de integración completo para el crew de 5 agentes.
    Mockea el LLM para simular la salida de cada agente en secuencia.
    """
    mock_litellm_completion_output = []
    for output in mock_llm_pipeline_output:
        mock_message = MagicMock()
        mock_message.content = output
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_litellm_completion_output.append(mock_response)

    litellm_completion_mock = mocker.patch("litellm.completion", side_effect=mock_litellm_completion_output)

    # Input inicial para la primera tarea del crew
    inputs = {"user_input_text": "Esta es la descripción de mi app de prueba.", "session_id": "test-session-123"}

    # Ejecutar el crew
    result = security_analysis_crew.kickoff(inputs=inputs)

    # Aserciones
    assert litellm_completion_mock.call_count == 5, "El LLM debe ser invocado una vez por cada uno de los 5 agentes."
    assert hasattr(result, "pydantic"), "El resultado debe tener el atributo .pydantic"
    assert isinstance(result.pydantic, FinalSecurityReport)
    assert result.pydantic.application_name == "App de Test para Crew"
    assert len(result.pydantic.prioritized_detectors) == 1
    assert result.pydantic.prioritized_detectors[0].detector_name == "Detector de Phishing Avanzado"
