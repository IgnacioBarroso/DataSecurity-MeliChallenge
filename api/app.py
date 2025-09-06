from fastapi import FastAPI
import api.auto_dotenv  # Fuerza la carga de .env
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routers import analysis
from api.routers import rag as rag_router
from pathlib import Path
import socket
import urllib.request
import json as _json
from src.config import settings
from fastapi.responses import ORJSONResponse
import time
from src.rag_system.retriever_factory import get_rag_chain


def create_app() -> FastAPI:
    app = FastAPI(
        title="DataSec AI Agent API",
        description="API para ejecutar el análisis de seguridad con agentes de IA.",
        version="1.1.0",
        default_response_class=ORJSONResponse,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
    app.include_router(rag_router.router, prefix="/api", tags=["RAG"])


    @app.get("/", summary="Endpoint de estado", tags=["Status"])
    def read_root():
        return {"status": "DataSec AI Agent API is running"}

    # La ingesta de DBIR se ejecuta como job separado vía docker-compose (dbir-ingest)
    # para evitar fallos en el arranque de la API y mejorar tiempos de inicio.

    # Servir el frontend estático en /ui
    app.mount("/ui", StaticFiles(directory="frontend", html=True), name="ui")

    @app.get("/health", summary="Healthcheck", tags=["Status"]) 
    def healthcheck():
        status = {
            "api": "ok",
            "redis": "configured" if settings.REDIS_HOST else "disabled",
            "vector_db": "present" if Path(settings.CHROMA_DB_PATH).exists() else "missing",
            "mcp": "configured" if settings.MCP_EXTERNAL_HOST else "disabled",
            "chroma": "unknown",
            "chroma_collection": "unknown",
            "chroma_count": "unknown",
        }
        # MCP DNS check
        try:
            if settings.MCP_EXTERNAL_HOST:
                socket.gethostbyname(settings.MCP_EXTERNAL_HOST)
                status["mcp_dns"] = "ok"
        except Exception:
            status["mcp_dns"] = "fail"
        # Chroma: primero intentamos vía SDK; si falla, intentamos REST
        try:
            if settings.CHROMA_DB_HOST and settings.CHROMA_DB_PORT:
                try:
                    import chromadb  # type: ignore
                    from chromadb.config import Settings as _ChromaCfg  # type: ignore
                    _cfg = _ChromaCfg(
                        chroma_api_impl="rest",
                        chroma_server_host=settings.CHROMA_DB_HOST,
                        chroma_server_http_port=settings.CHROMA_DB_PORT,
                    )
                    _client = chromadb.Client(_cfg)  # type: ignore
                    _col = _client.get_or_create_collection(settings.COLLECTION_NAME)
                    try:
                        _count = _col.count()  # type: ignore
                    except Exception:
                        _count = "unknown"
                    status["chroma"] = "ok"
                    status["chroma_collection"] = "present"
                    status["chroma_count"] = _count
                    return status
                except Exception:
                    pass
        except Exception:
            pass

        # Chroma REST basic check (v2 primero; fallback a v1 si no está disponible)
        def _try_check(api_base: str) -> tuple[str, str, str]:
            chroma_state = "unknown"; collection_state = "unknown"; count_state = "unknown"
            try:
                with urllib.request.urlopen(f"{api_base}/heartbeat", timeout=2) as r:
                    if r.status == 200:
                        chroma_state = "ok"
                with urllib.request.urlopen(f"{api_base}/collections", timeout=3) as r:
                    raw = r.read().decode("utf-8")
                    try:
                        data = _json.loads(raw)
                    except Exception:
                        data = {"raw": raw}
                    # Normalizar lista de colecciones
                    cols = []
                    if isinstance(data, dict) and "collections" in data:
                        cols = data.get("collections") or []
                    elif isinstance(data, list):
                        cols = data
                    # Buscar por nombre de colección
                    found = None
                    for c in cols:
                        if isinstance(c, dict) and c.get("name") == settings.COLLECTION_NAME:
                            found = c; break
                        if isinstance(c, str) and c == settings.COLLECTION_NAME:
                            found = {"id": c, "name": c}; break
                    if found:
                        collection_state = "present"
                        col_id = found.get("id") if isinstance(found, dict) else None
                        # Intentar contar ítems si existe endpoint
                        try:
                            if col_id:
                                with urllib.request.urlopen(f"{api_base}/collections/{col_id}/count", timeout=3) as rc:
                                    cdata = _json.loads(rc.read().decode("utf-8"))
                                    count = cdata.get("count")
                                    count_state = count if count is not None else "unknown"
                        except Exception:
                            count_state = "unknown"
                    else:
                        collection_state = "missing"
            except Exception:
                if chroma_state == "unknown":
                    chroma_state = "fail"
            return chroma_state, collection_state, count_state

        try:
            if settings.CHROMA_DB_HOST and settings.CHROMA_DB_PORT:
                base_v2 = f"http://{settings.CHROMA_DB_HOST}:{settings.CHROMA_DB_PORT}/api/v2"
                chroma_state, coll_state, cnt_state = _try_check(base_v2)
                if chroma_state == "fail":
                    base_v1 = f"http://{settings.CHROMA_DB_HOST}:{settings.CHROMA_DB_PORT}/api/v1"
                    chroma_state, coll_state, cnt_state = _try_check(base_v1)
                status["chroma"] = chroma_state
                status["chroma_collection"] = coll_state
                status["chroma_count"] = cnt_state
                if coll_state != "present" or cnt_state == "unknown":
                    # Fallback: intentar leer conteo desde el directorio persistente local
                    try:
                        import chromadb  # type: ignore
                        _pc = chromadb.PersistentClient(path=str(settings.CHROMA_DB_PATH))  # type: ignore
                        _col = _pc.get_or_create_collection(settings.COLLECTION_NAME)
                        status["chroma_collection"] = "present"
                        status["chroma_count"] = _col.count()  # type: ignore
                    except Exception:
                        pass
        except Exception:
            if status.get("chroma") == "unknown":
                status["chroma"] = "fail"
        return status

    # Warmup en modo TURBO
    if settings.is_turbo:
        try:
            t0 = time.perf_counter()
            chain = get_rag_chain()
            _ = chain.invoke("warmup")
            warm_ms = int((time.perf_counter() - t0) * 1000)
            print(f"[WARMUP] Turbo chain warmed in {warm_ms} ms")
        except Exception:
            pass

    return app
