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


def _strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        # remove first fence line
        s = "\n".join(s.splitlines()[1:])
    if s.endswith("```"):
        s = "\n".join(s.splitlines()[:-1])
    return s.strip()


def _parse_json_output(text: str) -> Dict[str, Any] | None:
    try:
        txt = _strip_code_fences(text)
        # Heurística: tomar del primer '{' al último '}'
        i = txt.find('{'); j = txt.rfind('}')
        if i != -1 and j != -1 and j > i:
            txt = txt[i:j+1]
        data = json.loads(txt)
        if isinstance(data, dict):
            return data
    except Exception:
        try:
            from json_repair import repair_json  # type: ignore
            repaired = repair_json(text)
            data = json.loads(repaired)
            if isinstance(data, dict):
                return data
        except Exception:
            return None
    return None


CACHE_VERSION = "v3"


def _normalize_report(data: Dict[str, Any]) -> Dict[str, Any]:
    # Post-procesamiento para asegurar estructura consistente
    try:
        plist = data.get("prioritized_detectors")
        if not isinstance(plist, list):
            plist = []
        # Normalizar cada detector
        norm_list = []
        for det in plist:
            if not isinstance(det, dict):
                continue
            name = det.get("detector_name") or det.get("name") or "Detector"
            desc = det.get("description") or ""
            steps = det.get("actionable_steps") or []
            if not isinstance(steps, list):
                steps = [str(steps)] if steps else []
            steps = [str(s) for s in steps][:3]
            while len(steps) < 3:
                steps.append("Add monitoring and alerting.")
            sev = (det.get("severity") or "Medium").title()
            if sev not in ("High", "Medium", "Low"):
                sev = "High" if sev.lower() == "critical" else "Medium"
            norm_list.append({
                "detector_name": str(name)[:120],
                "description": str(desc)[:600],
                "actionable_steps": steps,
                "severity": sev,
            })
        # Asegurar exactamente 5
        if len(norm_list) > 5:
            norm_list = norm_list[:5]
        while len(norm_list) < 5:
            norm_list.append({
                "detector_name": f"Additional Detector {len(norm_list)+1}",
                "description": "Additional control to harden the system.",
                "actionable_steps": [
                    "Instrument logs for this control.",
                    "Define alert thresholds.",
                    "Review weekly.",
                ],
                "severity": "Low",
            })
        data["prioritized_detectors"] = norm_list
    except Exception:
        pass
    return data


def run_turbo_pipeline(user_input: str) -> Dict[str, Any]:
    """
    Pipeline rápido sin CrewAI: recupera contexto DBIR y genera el reporte final JSON.
    Cachea resultados por pregunta normalizada + ingest_id.
    """
    assert settings.is_turbo, "Turbo pipeline debe llamarse solo en modo TURBO"

    # Cache lookup
    qn = _norm_question(user_input)
    cache_key = f"turbo:{CACHE_VERSION}:report:{_ingest_id()}:{hashlib.sha1(qn.encode('utf-8')).hexdigest()}"
    # Deshabilitar lectura de caché para evitar formatos legados
    cached = None

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
        'You are a senior cybersecurity reporter. Using ONLY the DBIR 2025 context, '
        'return a STRICT JSON object matching this structure: {{"report_id": string, "application_name": string, "summary": string, '
        '"prioritized_detectors": [ {{ "detector_name": string, "description": string, "actionable_steps": [string,string,string], '
        '"severity": one of ["High", "Medium", "Low"] }} ] }}. '
        'Requirements: 1) Output ONLY raw JSON (no prose, no markdown, no backticks). '
        '2) Include exactly 5 items in prioritized_detectors. 3) Each actionable_steps entry MUST be distinct (no duplicates). Keep concise.\n\n'
        'User Input: {user_input}\n\nContext:\n{context}\n\nJSON only:'
    )
    prompt = ChatPromptTemplate.from_template(template)
    # LLM con tokens acotados para turbo
    llm = ChatOpenAI(model=settings.OPENAI_MODEL_NAME, temperature=0.1, api_key=settings.OPENAI_API_KEY, max_tokens=384)

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
    data: Dict[str, Any] | None = _parse_json_output(out if isinstance(out, str) else str(out))
    if not isinstance(data, dict):
        data = {
            "report_id": "TURBO-REPORT",
            "application_name": "Turbo Analyzer",
            "summary": (out[:400] if isinstance(out, str) else ""),
            "prioritized_detectors": [],
            "_note": "Model returned non-JSON, fallback skeleton",
        }

    # Adjuntar métrica simple
    data.setdefault("_timing_ms", int(dt))
    # Normalizar y asegurar 5 detectores con severidades H/M/L
    data = _normalize_report(data)

    # Cachear 24h (después de normalizar)
    try:
        cache_set(cache_key, json.dumps(data, ensure_ascii=False), ttl_seconds=86400, host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
    except Exception:
        pass
    # Devolver el dict final para que el servicio lo serialice de forma consistente
    return data
