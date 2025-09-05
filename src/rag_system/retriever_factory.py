try:
    from langchain_chroma import Settings as ChromaSettings  # type: ignore
except Exception:
    ChromaSettings = None  # type: ignore
try:
    from langchain_cohere import CohereRerank
except Exception:
    CohereRerank = None

import math
import logging
from langchain_chroma import Chroma    
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from src.config import settings
from langchain.retrievers import ParentDocumentRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.rag_system.redis_docstore import RedisDocStore
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache

# Habilitar cache in-memory para LLM (aplica a heavy y turbo) para evitar repeticiones
try:
    set_llm_cache(InMemoryCache())
except Exception:
    pass

# Caches globales (por modo)
_CACHED_ADVANCED_RETRIEVER: dict[str, any] = {}
_CACHED_RAG_CHAIN: dict[str, any] = {}

def _build_vectorstore(chroma_path, collection_name, embedding_fn):
    chroma_host = getattr(settings, "CHROMA_DB_HOST", None)
    chroma_port = getattr(settings, "CHROMA_DB_PORT", None)

    if chroma_host and chroma_port and ChromaSettings:
        try:
            client_settings = ChromaSettings(
                chroma_api_impl="rest",
                chroma_server_host=chroma_host,
                chroma_server_http_port=chroma_port,
                anonymized_telemetry=False,
            )
            return Chroma(
                collection_name=collection_name,
                embedding_function=embedding_fn,
                client_settings=client_settings,
            )
        except Exception:
            pass  # Fallback a uso local si falla la config REST

    return Chroma(
        persist_directory=chroma_path,
        collection_name=collection_name,
        embedding_function=embedding_fn,
    )


def _make_base_retriever(vectorstore):
    """Devuelve retriever base con k acorde al modo."""
    k = 10 if settings.is_turbo else 20
    return vectorstore.as_retriever(search_kwargs={"k": k})


def create_advanced_retriever(chroma_path, collection_name, openai_api_key, cohere_api_key):
    mode_key = 'turbo' if settings.is_turbo else 'heavy'
    cached = _CACHED_ADVANCED_RETRIEVER.get(mode_key)
    if cached is not None:
        return cached
    # 1. Vectorstore
    embedding_fn = OpenAIEmbeddings(model="text-embedding-3-small", api_key=openai_api_key)
    vectorstore = _build_vectorstore(chroma_path, collection_name, embedding_fn)

    # 2. Base retriever: ParentDocumentRetriever si Redis está configurado, si no retriever simple
    redis_host = getattr(settings, "REDIS_HOST", None)
    redis_port = getattr(settings, "REDIS_PORT", None)
    redis_db = getattr(settings, "REDIS_DB", 0)
    if redis_host and redis_port is not None:
        docstore = RedisDocStore(host=redis_host, port=int(redis_port), db=int(redis_db))
        parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
        child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
        base_retriever = ParentDocumentRetriever(
            vectorstore=vectorstore,
            docstore=docstore,
            child_splitter=child_splitter,
            parent_splitter=parent_splitter,
        )
        logging.info("Usando ParentDocumentRetriever con RedisDocStore para las consultas.")
    else:
        base_retriever = _make_base_retriever(vectorstore)
        logging.info("Usando retriever de vectorstore simple (sin docstore persistente).")

    # 3. MultiQueryRetriever para expansión de consultas (deshabilitado en TURBO)
    if settings.is_turbo:
        advanced_retriever = base_retriever
    else:
        llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0, api_key=openai_api_key)
        advanced_retriever = MultiQueryRetriever.from_llm(retriever=base_retriever, llm=llm)

    # 4. ContextualCompressionRetriever con CohereRerank (opcional; deshabilitado en TURBO)
    if not settings.is_turbo and cohere_api_key and CohereRerank:
        # Wrapper simple con cache para Cohere rerank
        class CachedCompressor:
            def __init__(self, inner):
                self.inner = inner
                self._cache = {}
            def compress_documents(self, docs, query):
                try:
                    ids = tuple(getattr(d, 'metadata', {}).get('id') or hash(getattr(d, 'page_content','')) for d in docs)
                    key = (query, ids)
                    if key in self._cache:
                        return self._cache[key]
                except Exception:
                    key = None
                out = self.inner.compress_documents(docs, query)
                if key is not None:
                    self._cache[key] = out
                return out
        compressor = CachedCompressor(CohereRerank(
            cohere_api_key=cohere_api_key,
            model="rerank-english-v3.0",
            top_n=5,
        ))
        ret = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=advanced_retriever
        )
    else:
        if not settings.is_turbo:
            logging.warning(
                "Cohere API Key no configurada o paquete no disponible. Usando retriever sin compresión contextual."
            )
        ret = advanced_retriever
    _CACHED_ADVANCED_RETRIEVER[mode_key] = ret
    return ret

def get_rag_chain():
    mode_key = 'turbo' if settings.is_turbo else 'heavy'
    cached = _CACHED_RAG_CHAIN.get(mode_key)
    if cached is not None:
        return cached

    advanced_retriever = create_advanced_retriever(
        chroma_path=settings.CHROMA_DB_PATH,
        collection_name=settings.COLLECTION_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        cohere_api_key=(None if settings.is_turbo else getattr(settings, "COHERE_API_KEY", None))
    )

    template = """
    You are a senior cybersecurity analyst. Your task is to answer the user's question based ONLY on the following context from the Verizon DBIR 2025 report.
    Synthesize the information to provide a complete and precise answer. If the information is not present in the context, clearly state that you cannot answer.

    Context:
    {context}

    Question: {question}

    Answer:
    """
    prompt = ChatPromptTemplate.from_template(template)
    # Reducir max_tokens en modo TURBO para respuestas más breves
    llm = ChatOpenAI(
        model="gpt-4.1-nano",
        temperature=0.1,
        api_key=settings.OPENAI_API_KEY,
        max_tokens=256 if settings.is_turbo else None,
    )

    def cosine(a, b):
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(y*y for y in b))
        return dot / (na * nb + 1e-10)

    def mmr_rerank(question: str, docs, top_n: int = 5, lambda_mult: float = 0.5):
        try:
            emb = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY)
            q = emb.embed_query(question)
            # Limitar documentos a 20 para costo controlado
            docs = list(docs)[:20]
            D = [emb.embed_query(getattr(d, 'page_content', str(d))[:2000]) for d in docs]
            sims_q = [cosine(q, d) for d in D]
            selected = []
            selected_idx = []
            if not docs:
                return []
            # Primero: el más similar a la query
            first = max(range(len(docs)), key=lambda i: sims_q[i])
            selected.append(docs[first]); selected_idx.append(first)
            while len(selected) < min(top_n, len(docs)):
                best_i = None
                best_score = -1e9
                for i in range(len(docs)):
                    if i in selected_idx:
                        continue
                    max_sim_to_S = max(cosine(D[i], D[j]) for j in selected_idx) if selected_idx else 0.0
                    score = lambda_mult * sims_q[i] - (1 - lambda_mult) * max_sim_to_S
                    if score > best_score:
                        best_score = score; best_i = i
                if best_i is None:
                    break
                selected.append(docs[best_i]); selected_idx.append(best_i)
            return selected
        except Exception:
            # Si falla el reranking, devolver top 5 por similitud
            try:
                return docs[:5]
            except Exception:
                return docs

    def build_context(question: str):
        # Early-exit: si top1 muy alto, evitar fan-out pesado en heavy
        docs = []
        try:
            if not settings.is_turbo:
                # base retriever top1
                emb = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY)
                qv = emb.embed_query(question)
                vectorstore = _build_vectorstore(settings.CHROMA_DB_PATH, settings.COLLECTION_NAME, emb)
                base = _make_base_retriever(vectorstore)
                top1 = base.get_relevant_documents(question)
                def cosine(a, b):
                    import math
                    dot = sum(x*y for x, y in zip(a, b)); na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b)); return dot/(na*nb+1e-10)
                score = None
                if top1:
                    dv = emb.embed_query(getattr(top1[0], 'page_content', '')[:2000])
                    score = cosine(qv, dv)
                if score is not None and score >= 0.55:
                    docs = base.get_relevant_documents(question)
            if not docs:
                if hasattr(advanced_retriever, "invoke"):
                    docs = advanced_retriever.invoke(question)
                else:
                    docs = advanced_retriever.get_relevant_documents(question)
        except Exception:
            docs = []
        # Sin MMR en TURBO; en heavy mantenemos MMR si no hay Cohere
        if not settings.is_turbo and docs:
            use_cohere = bool(getattr(settings, "COHERE_API_KEY", None)) and CohereRerank is not None
            if not use_cohere:
                docs = mmr_rerank(question, docs, top_n=5)
        # Construir el contexto como texto concatenado
        texts = []
        for d in docs[:5]:
            content = getattr(d, 'page_content', str(d))
            texts.append(content)
        return "\n---\n".join(texts) if texts else ""

    rag_chain = (
        {"context": RunnableLambda(build_context), "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    _CACHED_RAG_CHAIN[mode_key] = rag_chain
    return rag_chain
