import chromadb
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config import GEMINI_API_KEY
import threading

# --- Constantes de Configuración ---
CHROMA_DB_PATH = "vector_db"
COLLECTION_NAME = "dbir_2025"
TOP_K_RESULTS = 5 # Número de resultados a recuperar

# Inicialización Singleton para el cliente y el modelo de embeddings
client = None
embeddings = None
collection = None
_lock = threading.Lock()

def _initialize_retriever():
    """Inicializa los componentes del retriever de forma segura para hilos."""
    global client, embeddings, collection
    if client is None:
        with _lock:
            if client is None: # Doble-check locking
                try:
                    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
                    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=GEMINI_API_KEY)
                    collection = client.get_collection(name=COLLECTION_NAME)
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
    _initialize_retriever()
    
    if collection is None:
        return "Error: La colección de la base de datos no está disponible. Asegúrate de que la ingesta se haya completado."

    try:
        # 1. Generar el embedding para la consulta del usuario
        query_embedding = embeddings.embed_query(query)

        # 2. Realizar la búsqueda de similitud en ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K_RESULTS
        )

        # 3. Formatear los resultados para el LLM
        if not results or not results.get('documents') or not results['documents'][0]:
            return "No se encontraron resultados relevantes en el informe DBIR para esta consulta."
        
        context_str = "Resultados recuperados del informe DBIR 2025:\n\n"
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            page_num = metadata.get('page_number', 'N/A')
            context_str += f"--- Fragmento {i+1} (Página: {page_num}) ---\n"
            context_str += doc
            context_str += "\n\n"
        
        return context_str.strip()

    except Exception as e:
        logging.error(f"Error durante la consulta a la base de datos vectorial: {e}")
        return "Se produjo un error al intentar recuperar información del informe DBIR."