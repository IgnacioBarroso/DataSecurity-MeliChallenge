from unittest.mock import MagicMock
from langchain_core.documents import Document

# --- Tests para dbir_rag_tool.py ---

def test_dbir_rag_query_tool_success(mocker):
    """Verifica que la herramienta RAG formatea correctamente los documentos recuperados."""
    # Mock de las dependencias externas
    mocker.patch("src.tools.dbir_rag_tool.GoogleGenerativeAIEmbeddings")
    mock_chroma_client = mocker.patch("src.tools.dbir_rag_tool.chromadb.PersistentClient")

    # Simular el retriever y su respuesta
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        'documents': [['Contenido del fragmento 1.', 'Contenido del fragmento 2.']],
        'metadatas': [[{'page_number': 1}, {'page_number': 2}]]
    }
    mock_chroma_client.return_value.get_collection.return_value = mock_collection

    # Importar la herramienta después de mockear
    from src.tools.dbir_rag_tool import dbir_rag_tool
    result = dbir_rag_tool.run("consulta de prueba")

    # Verificar que la salida es una concatenación de los contenidos y formato en inglés
    assert "Contenido del fragmento 1." in result
    assert "Contenido del fragmento 2." in result
    assert "--- Excerpt 1 (Page: 1) ---" in result
    assert "--- Excerpt 2 (Page: 2) ---" in result

# --- Tests para mitre_tool.py ---

def test_mitre_attack_query_tool_success(mocker):
    """Verifica que la herramienta de MITRE formatea correctamente los resultados."""
    # Mock de la dependencia externa
    mock_attack_cti = mocker.patch("src.tools.mitre_tool.attack")

    # Simular una técnica de MITRE
    mock_technique = MagicMock()
    mock_technique.id = "T1234"
    mock_technique.name = "Técnica de Prueba"
    mock_technique.description = "Esta es una descripción de prueba."
    mock_attack_cti.get_techniques_by_content.return_value = [mock_technique]

    # Importar la herramienta después de mockear
    from src.tools.mitre_tool import mitre_attack_query_tool
    result = mitre_attack_query_tool.run("phishing")

    assert "ID: T1234" in result
    assert "Nombre: Técnica de Prueba" in result

def test_mitre_attack_query_tool_no_results(mocker):
    """Verifica el mensaje cuando no se encuentran resultados."""
    mock_attack_cti = mocker.patch("src.tools.mitre_tool.attack")
    mock_attack_cti.get_techniques_by_content.return_value = []

    from src.tools.mitre_tool import mitre_attack_query_tool
    result = mitre_attack_query_tool.run("consulta inexistente")

    assert "No se encontraron técnicas de MITRE ATT&CK" in result