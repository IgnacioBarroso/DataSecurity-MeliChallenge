import os
import logging
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from src.rag_system.redis_docstore import RedisDocStore
from src.config import settings


# Configuración de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Constantes de Configuración ---
DBIR_PDF_PATH = "data/input/2025-dbir-data-breach-investigations-report.pdf"


def ingest_dbir_report():

    """
    Procesa el informe DBIR en PDF, lo divide jerárquicamente y lo indexa usando ParentDocumentRetriever.
    """
    if not os.path.exists(DBIR_PDF_PATH):
        logging.error(f"El informe DBIR no se encuentra en la ruta: {DBIR_PDF_PATH}")
        return

    logging.info(f"Iniciando la ingesta jerárquica del documento: {DBIR_PDF_PATH}")


    # 1. Cargar el documento PDF usando Unstructured
    try:
        loader = UnstructuredPDFLoader(file_path=DBIR_PDF_PATH, mode="elements")
        documents = loader.load()
        logging.info(f"Documento cargado exitosamente. {len(documents)} elementos extraídos.")
    except Exception as e:
        logging.error(f"Error al cargar el PDF con Unstructured: {e}")
        return

    # 1b. Filtrar metadatos complejos para compatibilidad con ChromaDB
    for doc in documents:
        if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
            doc.metadata = clean_metadata(doc.metadata)

    # 1c. Validar dimensiones del modelo de embedding vs Chroma
    # (Esto se valida automáticamente en Chroma/OpenAIEmbeddings, pero se puede loggear)
    embedding_model = "text-embedding-3-small"
    from pydantic import SecretStr
    embedding = OpenAIEmbeddings(model=embedding_model, api_key=SecretStr(settings.OPENAI_API_KEY))
    expected_dim = 1536
    logging.info(f"Usando modelo de embedding '{embedding_model}' con dimensión esperada: {expected_dim}")

    # 2. Definir los splitters jerárquicos
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

    # 3. Configurar el vectorstore y el docstore (remoto si hay host/port)
    chroma_host = getattr(settings, "CHROMA_DB_HOST", None)
    chroma_port = getattr(settings, "CHROMA_DB_PORT", None)
    try:
        from langchain_chroma import Settings as ChromaSettings
    except ImportError:
        ChromaSettings = None
    if chroma_host and chroma_port and ChromaSettings:
        client_settings = ChromaSettings(
            chroma_api_impl="rest",
            chroma_server_host=chroma_host,
            chroma_server_http_port=chroma_port,
            anonymized_telemetry=False
        )
        vectorstore = Chroma(
            collection_name=settings.COLLECTION_NAME,
            embedding_function=embedding,
            client_settings=client_settings
        )
    else:
        vectorstore = Chroma(
            collection_name=settings.COLLECTION_NAME,
            embedding_function=embedding,
            persist_directory=settings.CHROMA_DB_PATH
        )
    # Docstore: Redis si está configurado, de lo contrario memoria
    redis_host = getattr(settings, "REDIS_HOST", None)
    redis_port = getattr(settings, "REDIS_PORT", None)
    redis_db = getattr(settings, "REDIS_DB", 0)
    if redis_host and redis_port is not None:
        store = RedisDocStore(host=redis_host, port=int(redis_port), db=int(redis_db))
        logging.info(f"Usando RedisDocStore en {redis_host}:{redis_port}/{redis_db}")
    else:
        store = InMemoryStore()

    # 4. Instanciar y poblar el ParentDocumentRetriever
    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=store,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )
    logging.info("Añadiendo documentos al retriever. Este proceso realizará la división y vectorización...")
    retriever.add_documents(documents)
    logging.info("--- Ingesta jerárquica completada exitosamente! ---")


# --- Filtro robusto de metadatos para ChromaDB ---
def clean_metadata(metadata: dict) -> dict:
    # Solo conservar claves relevantes y valores simples
    allowed_keys = {'page_number', 'source', 'section', 'title', 'text', 'filename', 'filetype', 'category', 'subsection', 'author', 'date'}
    clean = {}
    for k, v in metadata.items():
        if k in allowed_keys and isinstance(v, (str, int, float, bool)):
            clean[k] = v
        # Si la clave es relevante pero el valor es complejo, lo convertimos a string
        elif k in allowed_keys:
            clean[k] = str(v)
        # Si la clave no es relevante pero el valor es simple, lo dejamos solo si no hay nada mejor
        elif isinstance(v, (str, int, float, bool)):
            clean[k] = v
    return clean

if __name__ == "__main__":
    ingest_dbir_report()
