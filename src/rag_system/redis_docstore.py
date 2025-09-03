from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Tuple

import redis
try:
    from langchain_core.documents import Document  # type: ignore
except Exception:
    Document = None  # type: ignore


class RedisDocStore:
    """
    DocStore compatible con ParentDocumentRetriever basado en Redis.

    Guarda por clave (doc_id) un JSON con page_content y metadata opcional.
    Implementa métodos mínimos usados por LangChain: mset, mget, set, get, delete, yield_keys.
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, prefix: str = "doc:"):
        self._r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self._prefix = prefix

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def set(self, key: str, value: Any) -> None:
        payload = self._to_payload(value)
        self._r.set(self._k(key), payload)

    def mset(self, kvs: Dict[str, Any]) -> None:
        if not kvs:
            return
        pipe = self._r.pipeline()
        for k, v in kvs.items():
            pipe.set(self._k(k), self._to_payload(v))
        pipe.execute()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        raw = self._r.get(self._k(key))
        return json.loads(raw) if raw else None

    def mget(self, keys: Iterable[str]) -> List[Optional[Dict[str, Any]]]:
        ks = [self._k(k) for k in keys]
        vals = self._r.mget(ks)
        out: List[Optional[Dict[str, Any]]] = []
        for v in vals:
            out.append(json.loads(v) if v else None)
        return out

    def delete(self, keys: Iterable[str]) -> None:
        ks = [self._k(k) for k in keys]
        if ks:
            self._r.delete(*ks)

    def yield_keys(self, prefix: str = "") -> Iterable[str]:
        patt = self._k(prefix) + "*"
        for k in self._r.scan_iter(match=patt):
            yield k.removeprefix(self._prefix)

    @staticmethod
    def _to_payload(value: Any) -> str:
        # Value puede ser string, Document o dict similar
        if Document and isinstance(value, Document):
            data = {"page_content": value.page_content, "metadata": value.metadata or {}}
            return json.dumps(data, ensure_ascii=False)
        if isinstance(value, dict) and "page_content" in value:
            return json.dumps(value, ensure_ascii=False)
        # Fallback: guardar como texto
        return json.dumps({"page_content": str(value), "metadata": {}}, ensure_ascii=False)
