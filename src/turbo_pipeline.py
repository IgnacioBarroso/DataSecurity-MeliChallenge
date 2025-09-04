from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict

from src.config import settings
from src.cache import cache_get, cache_set
from src.rag_system.retriever_factory import create_advanced_retriever
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda


def _norm_question(q: str) -> str:
    q = (q or "").strip().lower()
    # quitar tildes simples
    repl = ("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")
    for a, b in repl:
        q = q.replace(a, b)
    return " ".join(q.split())[:300]


def _ingest_id() -> str:
    # versionar por path + nombre de colección
    raw = f"{settings.CHROMA_DB_PATH}:{settings.COLLECTION_NAME}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def run_turbo_pipeline(user_input: str) -> Dict[str, Any]:
    """
    Pipeline rápido sin CrewAI: recupera contexto DBIR y genera el reporte final JSON.
    Cachea resultados por pregunta normalizada + ingest_id.
    """
    assert settings.is_turbo, "Turbo pipeline debe llamarse solo en modo TURBO"

    # Cache lookup
    qn = _norm_question(user_input)
    cache_key = f"turbo:report:{_ingest_id()}:{hashlib.sha1(qn.encode('utf-8')).hexdigest()}"
    cached = cache_get(cache_key, host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
    if cached:
        try:
            data = json.loads(cached)
            return {"report_json": json.dumps(data, ensure_ascii=False), "session_id": None, "cached": True}
        except Exception:
            pass

    # Build retriever once (factory ya cachea en TURBO)
    retriever = create_advanced_retriever(
        chroma_path=settings.CHROMA_DB_PATH,
        collection_name=settings.COLLECTION_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        cohere_api_key=None,
    )

    def build_context(question: str) -> str:
        try:
            if hasattr(retriever, "invoke"):
                docs = retriever.invoke(question)
            else:
                docs = retriever.get_relevant_documents(question)
        except Exception:
            docs = []
        texts = []
        for d in list(docs)[:5]:
            content = getattr(d, "page_content", str(d))
            texts.append(content)
        return "\n---\n".join(texts)

    # Prompt compacto orientado a JSON FinalReport
    template = (
        "You are a senior cybersecurity reporter. Using ONLY the following DBIR 2025 context, "
        "generate a valid JSON FinalReport with fields: report_id, application_name, summary, prioritized_detectors[]. "
        "Each detector must include detector_name, description, actionable_steps (3 items), severity. "
        "Be concise and factual. If context is insufficient, state it clearly, but still return a valid JSON skeleton.\n\n"
        "User Input: {user_input}\n\nContext:\n{context}\n\nJSON:"
    )
    prompt = ChatPromptTemplate.from_template(template)
    # LLM con tokens acotados para turbo
    llm = ChatOpenAI(model=settings.OPENAI_MODEL_NAME, temperature=0.1, api_key=settings.OPENAI_API_KEY, max_tokens=256)

    chain = (
        {"context": RunnableLambda(build_context), "user_input": RunnableLambda(lambda x: user_input)}
        | prompt
        | llm
        | StrOutputParser()
    )

    t0 = time.perf_counter()
    out = chain.invoke(qn)
    dt = (time.perf_counter() - t0) * 1000.0

    # Normalizar a JSON estricto
    data: Dict[str, Any]
    try:
        data = json.loads(out)
        if not isinstance(data, dict):
            raise ValueError("not a dict")
    except Exception:
        data = {
            "report_id": "TURBO-REPORT",
            "application_name": "Turbo Analyzer",
            "summary": out[:400] if isinstance(out, str) else "",
            "prioritized_detectors": [],
            "_note": "Model returned non-JSON, fallback skeleton",
        }

    # Cachear 24h
    try:
        cache_set(cache_key, json.dumps(data, ensure_ascii=False), ttl_seconds=86400, host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
    except Exception:
        pass

    # Adjuntar métrica simple
    data.setdefault("_timing_ms", int(dt))
    return {"report_json": json.dumps(data, ensure_ascii=False), "session_id": None}

