
import os
import logging
import chromadb
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config import GEMINI_API_KEY, CHROMA_DB_PATH, COLLECTION_NAME

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constantes de Configuración ---
DBIR_PDF_PATH = "data/input/2025-dbir-data-breach-investigations-report.pdf"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

def ingest_dbir_report():
    """
    Procesa el informe DBIR en PDF, lo divide en fragmentos, genera embeddings y los almacena en ChromaDB.
    """
    if not os.path.exists(DBIR_PDF_PATH):
        logging.error(f"El informe DBIR no se encuentra en la ruta: {DBIR_PDF_PATH}")
        return

    logging.info(f"Iniciando la ingesta del documento: {DBIR_PDF_PATH}")

    # 1. Cargar el documento PDF usando Unstructured
    try:
        loader = UnstructuredPDFLoader(file_path=DBIR_PDF_PATH, mode="elements")
        documents = loader.load()
        logging.info(f"Documento cargado exitosamente. {len(documents)} elementos extraídos.")
    except Exception as e:
        logging.error(f"Error al cargar el PDF con Unstructured: {e}")
        return

    # 2. Dividir el texto en fragmentos (chunks)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    logging.info(f"Documento dividido en {len(chunks)} fragmentos.")

    if not chunks:
        logging.error("No se generaron fragmentos del documento. Verifique el contenido del PDF.")
        return

    # 3. Configurar el modelo de embeddings
    try:
    embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004", google_api_key=GEMINI_API_KEY)
    except Exception as e:
        logging.error(f"Error al inicializar el modelo de embeddings: {e}")
        return

    # 4. Crear o cargar la base de datos vectorial ChromaDB persistente
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        # Borra la colección si ya existe para asegurar una ingesta limpia
        if COLLECTION_NAME in [c.name for c in client.list_collections()]:
            logging.warning(f"La colección '{COLLECTION_NAME}' ya existe. Se eliminará y se volverá a crear.")
            client.delete_collection(name=COLLECTION_NAME)
        
        collection = client.create_collection(name=COLLECTION_NAME)
        logging.info(f"Colección '{COLLECTION_NAME}' creada/cargada en ChromaDB.")
    except Exception as e:
        logging.error(f"Error al conectar con ChromaDB: {e}")
        return

    # 5. Generar embeddings y almacenar en la colección
    logging.info("Generando embeddings y guardando en la base de datos. Esto puede tardar unos minutos...")
    
    total_chunks = len(chunks)
    for i, chunk in enumerate(chunks):
        try:
            # Extraer contenido y metadatos
            content = chunk.page_content
            metadata = chunk.metadata
            
            # Crear un ID único para el chunk
            chunk_id = f"chunk_{i}"
            
            # Generar embedding para el contenido
            embedding = embeddings.embed_query(content)
            
            # Añadir a la colección de ChromaDB
            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            
            if (i + 1) % 100 == 0:
                logging.info(f"Procesado {i + 1}/{total_chunks} fragmentos...")

        except Exception as e:
            logging.error(f"Error procesando el fragmento {i}: {e}")
            continue

    logging.info("--- ¡Ingesta completada exitosamente! ---")
    logging.info(f"Total de fragmentos en la colección '{COLLECTION_NAME}': {collection.count()}")

if __name__ == "__main__":
    ingest_dbir_report()
