from fastapi import FastAPI
import api.auto_dotenv  # Fuerza la carga de .env
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routers import analysis
from api.routers import rag as rag_router
from pathlib import Path
import socket


def create_app() -> FastAPI:
    app = FastAPI(
        title="DataSec AI Agent API",
        description="API para ejecutar el análisis de seguridad con agentes de IA.",
        version="1.1.0",
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
        from src.config import settings
        import urllib.request
        import json as _json
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
        # Chroma REST basic check
        try:
            if settings.CHROMA_DB_HOST and settings.CHROMA_DB_PORT:
                base = f"http://{settings.CHROMA_DB_HOST}:{settings.CHROMA_DB_PORT}/api/v1"
                with urllib.request.urlopen(f"{base}/heartbeat", timeout=2) as r:
                    if r.status == 200:
                        status["chroma"] = "ok"
                # Check collection
                with urllib.request.urlopen(f"{base}/collections", timeout=3) as r:
                    data = _json.loads(r.read().decode("utf-8"))
                    cols = data.get("collections", [])
                    found = next((c for c in cols if c.get("name") == settings.COLLECTION_NAME), None)
                    if found:
                        status["chroma_collection"] = "present"
                        col_id = found.get("id")
                        # Intentar contar ítems (si endpoint disponible)
                        try:
                            with urllib.request.urlopen(f"{base}/collections/{col_id}/count", timeout=3) as rc:
                                cdata = _json.loads(rc.read().decode("utf-8"))
                                # Algunos retornan {"count": N}
                                count = cdata.get("count")
                                status["chroma_count"] = count if count is not None else "unknown"
                        except Exception:
                            # Fallback: intenta /get con limit 0 para obtener metadatos (puede no estar soportado)
                            status["chroma_count"] = "unknown"
                    else:
                        status["chroma_collection"] = "missing"
        except Exception:
            if status.get("chroma") == "unknown":
                status["chroma"] = "fail"
        return status

    return app
