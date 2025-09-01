import chromadb
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config import GEMINI_API_KEY, CHROMA_DB_PATH, COLLECTION_NAME
import threading

from crewai.tools import BaseTool

# --- Constantes de Configuración ---
TOP_K_RESULTS = 5 # Número de resultados a recuperar

# Inicialización Singleton para el cliente y el modelo de embeddings
_client = None
_embeddings = None
_collection = None
_lock = threading.Lock()

def _initialize_retriever():
    """Inicializa los componentes del retriever de forma segura para hilos."""
    global _client, _embeddings, _collection
    if _client is None:
        with _lock:
            if _client is None: # Doble-check locking
                try:
                    _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
                    _embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004", google_api_key=GEMINI_API_KEY)
                    _collection = _client.get_collection(name=COLLECTION_NAME)
                    logging.info("Retriever inicializado y conectado a ChromaDB.")
                except Exception as e:
                    logging.error(f"Error al inicializar el retriever. ¿Ejecutaste el script de ingesta? Error: {e}")
                    raise

def query_dbir_report(query: str) -> str:
    """
    Realiza una consulta a la base de datos vectorial del DBIR y devuelve los resultados más relevantes.

    Args:
        query: La pregunta o término de búsqueda.

    Returns:
        Una cadena formateada con los fragmentos de texto más relevantes encontrados.
    """
    try:
        _initialize_retriever()
        if _collection is None:
            return "Error: The database collection is not available. Make sure ingestion has been completed."

        # 1. Generate embedding for the user query
        query_embedding = _embeddings.embed_query(query)

        # 2. Perform similarity search in ChromaDB
        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K_RESULTS
        )

        # 3. Format results for the LLM
        if not results or not results.get('documents') or not results['documents'][0]:
            return "No relevant results found in the DBIR report for this query."
        
        context_str = "Results retrieved from the DBIR 2025 report:\n\n"
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            page_num = metadata.get('page_number', 'N/A')
            context_str += f"--- Excerpt {i+1} (Page: {page_num}) ---\n"
            context_str += doc
            context_str += "\n\n"
        
        return context_str.strip()

    except Exception as e:
        logging.error(f"Error during vector database query: {e}")
        return "An error occurred while retrieving information from the DBIR report."


class DBIRReportQueryTool(BaseTool):
    name: str = "DBIR Report RAG Tool"
    description: str = (
        "Úsala para hacer preguntas específicas al informe DBIR 2025 de Verizon. "
        "Esta herramienta es tu única fuente de conocimiento sobre tendencias de amenazas, "
        "vectores de ataque, estadísticas de brechas y patrones de incidentes. "
        "Formula preguntas claras y concisas para obtener la información más relevante."
    )

    def _run(self, query: str) -> str:
        """Ejecuta una consulta contra el sistema RAG del DBIR."""
        return query_dbir_report(query)

# Instancia única de la herramienta para ser importada
dbir_rag_tool = DBIRReportQueryTool()