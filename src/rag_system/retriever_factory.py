import logging
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere import CohereRerank
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from src.config import settings

def create_advanced_retriever(chroma_path, collection_name, openai_api_key, cohere_api_key):
    # 1. Cargar el vectorstore persistente
    vectorstore = Chroma(
        persist_directory=chroma_path,
        collection_name=collection_name,
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_api_key)
    )

    # 2. Recuperador base (por ahora, solo vectorstore)
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})

    # 3. MultiQueryRetriever para expansión de consultas
    llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0, openai_api_key=openai_api_key)
    multi_query_retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever, llm=llm
    )

    # 4. ContextualCompressionRetriever con CohereRerank
    compressor = CohereRerank(cohere_api_key=cohere_api_key, top_n=5)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=multi_query_retriever
    )

    return compression_retriever

def get_rag_chain():
    advanced_retriever = create_advanced_retriever(
        chroma_path=settings.CHROMA_DB_PATH,
        collection_name=settings.COLLECTION_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        cohere_api_key=getattr(settings, "COHERE_API_KEY", None)
    )

    template = """
    Eres un analista experto en ciberseguridad. Tu tarea es responder a la pregunta basándote ÚNICAMENTE en el siguiente contexto del reporte DBIR 2025.
    Sintetiza la información para dar una respuesta completa y precisa. Si la información no está en el contexto, indica que no se puede responder.

    Contexto:
    {context}

    Pregunta: {question}

    Respuesta:
    """
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.1, openai_api_key=settings.OPENAI_API_KEY)

    rag_chain = (
        {"context": advanced_retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain
