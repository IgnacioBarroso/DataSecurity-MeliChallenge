from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict

from src.config import settings
from src.models import FinalReport
from src.cache import cache_get, cache_set
from src.rag_system.retriever_factory import create_advanced_retriever
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
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
    # Post-procesamiento: normaliza campos y elimina duplicados sin añadir placeholders
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
            # Deduplicar pasos (por similitud si está disponible)
            try:
                from rapidfuzz import fuzz  # type: ignore
                deduped: list[str] = []
                for s in [str(s).strip() for s in steps if str(s).strip()]:
                    if not deduped:
                        deduped.append(s)
                        continue
                    if max((fuzz.ratio(s.lower(), t.lower()) for t in deduped), default=0) < 90:
                        deduped.append(s)
                steps = deduped
            except Exception:
                seen = set()
                deduped = []
                for s in [str(s).strip().lower() for s in steps if str(s).strip()]:
                    if s not in seen:
                        seen.add(s); deduped.append(s)
                steps = deduped
            # Completar hasta 3 pasos con buenas prácticas no redundantes (si faltan)
            if len(steps) < 3:
                pool = [
                    "Enable multi-factor authentication.",
                    "Enforce least privilege on roles.",
                    "Instrument tamper-evident logging.",
                    "Define alert thresholds and automate notifications.",
                    "Encrypt sensitive data at rest and in transit.",
                    "Schedule periodic access reviews.",
                    "Deploy anomaly detection on APIs.",
                ]
                for fb in pool:
                    if len(steps) >= 3:
                        break
                    low = [x.lower() for x in steps]
                    if fb.lower() not in low:
                        steps.append(fb)
            # Cortar a 3
            steps = steps[:3]
            sev = (det.get("severity") or "Medium").title()
            if sev not in ("High", "Medium", "Low"):
                sev = "High" if sev.lower() == "critical" else "Medium"
            norm_list.append({
                "detector_name": str(name)[:120],
                "description": str(desc)[:600],
                "actionable_steps": steps,
                "severity": sev,
            })
        # No añadir placeholders; el asegurado de 5 se hará luego con contexto
        if len(norm_list) > 5:
            norm_list = norm_list[:5]
        data["prioritized_detectors"] = norm_list
    except Exception:
        pass
    return data


def _derive_detectors_from_docs(docs: list, existing_names: set[str], needed: int) -> list[Dict[str, Any]]:
    out: list[Dict[str, Any]] = []
    if not docs or needed <= 0:
        return out
    def clean_brackets(s: str) -> str:
        import re
        return re.sub(r"\[[^\]]+\]", "", s).strip()
    def title_from_doc(d) -> str:
        meta = getattr(d, 'metadata', {}) or {}
        # Preferir título/section del documento si existe
        for key in ('title', 'section', 'subsection'):
            val = meta.get(key)
            if isinstance(val, str) and val.strip():
                t = clean_brackets(val)
                if len(t) >= 6:
                    return t[:120]
        # Fallback: tomar primera línea del contenido
        txt = getattr(d, 'page_content', '') or ''
        first = (txt.strip().split("\n", 1)[0]).strip()
        first = clean_brackets(first)
        words = first.split()
        # Evitar encabezados que empiezan con conectores sueltos
        while words and words[0].lower() in {"of", "and", "or", "the", "a", "an"}:
            words = words[1:]
        name = " ".join(words[:8]) if words else "Threat Detector"
        return name or "Threat Detector"
    def severity_from_text(txt: str) -> str:
        t = txt.lower()
        if any(k in t for k in ["ransomware", "breach", "critical", "compromise", "exfiltration"]):
            return "High"
        if any(k in t for k in ["credential", "phishing", "sql", "xss", "ddos", "lateral"]):
            return "Medium"
        return "Low"
    def steps_from_text(txt: str) -> list[str]:
        t = txt.lower()
        steps: list[str] = []
        if "credential" in t or "password" in t:
            steps += ["Enable MFA everywhere.", "Enforce strong password policies.", "Monitor auth anomalies."]
        if "phishing" in t or "email" in t:
            steps += ["Deploy phishing-resistant MFA.", "Run phishing awareness campaigns.", "Enable attachment sandboxing."]
        if "api" in t or "endpoint" in t:
            steps += ["Enforce authN/Z on APIs.", "Rate-limit and WAF for APIs.", "Log and monitor API calls."]
        if "cloud" in t or "s3" in t or "bucket" in t:
            steps += ["Audit cloud IAM and policies.", "Enable CloudTrail/Config rules.", "Block public buckets by default."]
        if not steps:
            steps = [
                "Harden configurations and patch.",
                "Instrument security logging.",
                "Define alert thresholds and response runbooks.",
            ]
        # dedupe & cut
        dedup = []
        seen = set()
        for s in steps:
            k = s.lower()
            if k not in seen:
                seen.add(k); dedup.append(s)
            if len(dedup) >= 3:
                break
        return dedup
    for d in docs:
        if len(out) >= needed:
            break
        txt = getattr(d, 'page_content', str(d))
        name = title_from_doc(d)
        base_name = name
        i = 2
        while name.lower() in existing_names:
            name = f"{base_name} #{i}"; i += 1
        # Descripción: preferir un snippet legible que no sea idéntico al nombre
        flat = " ".join((txt or "").strip().split())
        desc = flat[:400]
        if not desc or desc.lower().startswith(name.lower()):
            # intentar a partir de la segunda oración
            import re
            sentences = re.split(r"(?<=[\.!?])\s+", flat)
            if len(sentences) > 1:
                cand = sentences[1]
                desc = (cand[:400] if cand else desc) or desc
        sev = severity_from_text(txt)
        steps = steps_from_text(txt)
        out.append({
            "detector_name": name,
            "description": desc,
            "actionable_steps": steps,
            "severity": sev,
        })
        existing_names.add(name.lower())
    return out


def run_turbo_pipeline(user_input: str) -> Dict[str, Any]:
    """
    Pipeline rápido sin CrewAI: recupera contexto DBIR y genera el reporte final JSON.
    Cachea resultados por pregunta normalizada + ingest_id.
    """
    # Permitir invocación explícita desde el endpoint con `mode=turbo`,
    # independientemente del valor global de `ANALYZER_MODE`.

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
        force_turbo=True,
    )

    last_docs: list | None = None
    def build_context(question: str) -> str:
        nonlocal last_docs
        try:
            if hasattr(retriever, "invoke"):
                docs = retriever.invoke(question)
            else:
                docs = retriever.get_relevant_documents(question)
        except Exception:
            docs = []
        last_docs = list(docs) if docs else []
        texts = []
        for d in list(docs)[:5]:
            content = getattr(d, "page_content", str(d))
            texts.append(content)
        return "\n---\n".join(texts)

    # Prompt compacto con reglas de calidad (JSON estricto, exactamente 5 detectores)
    template = (
        'You are a senior cybersecurity reporter. Using ONLY the DBIR 2025 context, '
        'return a STRICT JSON FinalReport with fields: report_id (string), application_name (string), summary (string), '
        'prioritized_detectors (list of exactly 5 Detector objects). Detector rules: '
        'name is a concise technical noun phrase (8–120 chars, not narrative), description is specific (40–600 chars, not equal to name; aim 60–120 chars), '
        'actionable_steps has exactly 3 distinct items, severity is one of ["High","Medium","Low"]. '
        'Output ONLY raw JSON (no prose, no markdown, no backticks).\n\n'
        '{format_instructions}\n\n'
        'User Input: {user_input}\n\nContext:\n{context}\n'
    )
    prompt = ChatPromptTemplate.from_template(template)
    # LLM con tokens acotados para turbo
    llm = ChatOpenAI(model=settings.OPENAI_MODEL_NAME, temperature=0.1, api_key=settings.OPENAI_API_KEY, max_tokens=1024)

    json_parser = JsonOutputParser()
    fmt_instructions = (
        'Format: a single JSON object with EXACTLY these top-level keys: '
        '"report_id", "application_name", "summary", "prioritized_detectors". '
        'The value of "prioritized_detectors" is an array of up to 5 objects where each object has keys '
        '"detector_name" (8-120 chars noun phrase), "description" (40-600 chars), '
        '"actionable_steps" (array with exactly 3 strings), and "severity" ("High"|"Medium"|"Low").'
    )
    chain_json = (
        {"context": RunnableLambda(build_context), "user_input": RunnableLambda(lambda x: user_input), "format_instructions": RunnableLambda(lambda _: fmt_instructions)}
        | prompt
        | llm
        | json_parser
    )
    chain_text = (
        {"context": RunnableLambda(build_context), "user_input": RunnableLambda(lambda x: user_input), "format_instructions": RunnableLambda(lambda _: fmt_instructions)}
        | prompt
        | llm
        | StrOutputParser()
    )

    t0 = time.perf_counter()
    try:
        out = chain_json.invoke(qn)
    except Exception:
        out = chain_text.invoke(qn)
    dt = (time.perf_counter() - t0) * 1000.0

    # Parse y validar con Pydantic; un reintento si falla
    if isinstance(out, dict):
        data: Dict[str, Any] | None = out
    else:
        data = _parse_json_output(out if isinstance(out, str) else str(out))
    def _valid(fr: Dict[str, Any]) -> bool:
        try:
            FinalReport.model_validate(fr)
            return True
        except Exception:
            return False
    if not isinstance(data, dict) or not _valid(data):
        try:
            repair_tmpl = (
                'Your previous output did not validate against the FinalReport + Detector constraints. '
                'Return a STRICT valid JSON with the exact keys and shapes described here: {format_instructions}\n\n'
                'User Input: {user_input}\n\nContext:\n{context}\n'
            )
            repair_prompt = ChatPromptTemplate.from_template(repair_tmpl)
            repair_chain = (
                {"context": RunnableLambda(build_context), "user_input": RunnableLambda(lambda x: user_input), "format_instructions": RunnableLambda(lambda _: fmt_instructions)}
                | repair_prompt
                | llm
                | json_parser
            )
            out2 = repair_chain.invoke(qn)
            data = out2 if isinstance(out2, dict) else _parse_json_output(out2)
        except Exception:
            data = None
    if not isinstance(data, dict):
        data = {"report_id": "TURBO-REPORT", "application_name": "Turbo Analyzer", "summary": "", "prioritized_detectors": []}
    # Re-validar y manejar envoltorio común {'FinalReport': {...}}
    if isinstance(data, dict) and (not _valid(data)) and set(data.keys()) == {"FinalReport"} and isinstance(data.get("FinalReport"), dict):
        inner = data.get("FinalReport")
        if isinstance(inner, dict) and _valid(inner):
            data = inner

    # Adjuntar métrica simple y limpiar claves extra
    data.pop("_timing_ms", None)
    data.pop("_note", None)
    data["timing_ms"] = int(dt)
    # Recortar a 5 si el modelo devolvió más (no inventar ítems si faltan)
    try:
        plist = data.get("prioritized_detectors") or []
        if isinstance(plist, list) and len(plist) > 5:
            data["prioritized_detectors"] = plist[:5]
    except Exception:
        pass

    # Cachear 24h (después de normalizar y completar)
    try:
        cache_set(cache_key, json.dumps(data, ensure_ascii=False), ttl_seconds=86400, host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
    except Exception:
        pass
    # Devolver el dict final para que el servicio lo serialice de forma consistente
    return data
