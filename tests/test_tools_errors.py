import pytest
from unittest.mock import patch, MagicMock
from src.tools.dbir_rag_tool import (
    dbir_rag_tool,
)  # Importar la instancia de la herramienta
from src.tools.mitre_tool import mitre_attack_query_tool, get_attack_client

# ===================== TESTS DE ERRORES Y CASOS LÍMITE EN TOOLS =====================


@pytest.mark.parametrize(
    "query,expected_error",
    [
        (
            "vector de amenaza inexistente",
            "No se encontraron resultados relevantes en el informe DBIR",
        ),
        (
            "",
            "Error: La colección de la base de datos no está disponible. Asegúrate de que la ingesta se haya completado.",
        ),
    ],
)
def test_dbir_rag_tool_error_handling(query, expected_error):
    print("\033[91m[TEST ERROR] Probando error en DBIR RAG Tool:\033[0m", repr(query))
    with patch(
        "src.tools.dbir_rag_tool.query_dbir_report", return_value=expected_error
    ):
        # Llamar al método .run() de la instancia de la herramienta
        result = dbir_rag_tool.run(query)
        assert expected_error in result


@pytest.mark.parametrize(
    "query,expected_error",
    [
        (
            "técnica mitre inexistente",
            "No se encontraron técnicas de MITRE ATT&CK para la consulta",
        ),
        (None, "Ocurrió un error al buscar en MITRE ATT&CK"),
    ],
)
def test_mitre_attack_query_tool_error_handling(query, expected_error):
    print("\033[91m[TEST ERROR] Probando error en MITRE Tool:\033[0m", repr(query))
    # Patch get_attack_client().get_techniques_by_content para simular error o resultado vacío
    mock_attack_client = MagicMock()
    if query is None:
        mock_attack_client.get_techniques_by_content.side_effect = Exception(
            "Simulado error de MITRE"
        )
    else:
        mock_attack_client.get_techniques_by_content.return_value = []
    with patch(
        "src.tools.mitre_tool.get_attack_client", return_value=mock_attack_client
    ):
        result = mitre_attack_query_tool.run(query)
        assert expected_error in result


@patch(
    "stix2.datastore.taxii.TAXIICollectionSource"
)  # Mockear la clase que hace la llamada de red
@patch("taxii2client.v21.Collection")  # Mockear la colección
def test_get_attack_client_singleton(mock_collection_class, mock_taxii_source_class):
    """Verifica que get_attack_client devuelve la misma instancia (singleton)."""
    # Configurar el mock de la colección para que no intente hacer llamadas de red
    mock_collection_instance = MagicMock()
    mock_collection_instance.can_read = True  # Simular que puede leer
    mock_collection_class.return_value = mock_collection_instance

    # Configurar el mock de TAXIICollectionSource para que no intente hacer llamadas de red
    mock_taxii_source_instance = MagicMock()
    mock_taxii_source_class.return_value = mock_taxii_source_instance

    client1 = get_attack_client()
    client2 = get_attack_client()
    assert client1 is client2
