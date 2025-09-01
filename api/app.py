
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import analysis

def create_app() -> FastAPI:
    app = FastAPI(
        title="DataSec AI Agent API",
        description="API para ejecutar el análisis de seguridad con agentes de IA.",
        version="1.1.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(analysis.router, prefix="/api", tags=["Analysis"])

    @app.get("/", summary="Endpoint de estado", tags=["Status"])
    def read_root():
        return {"status": "DataSec AI Agent API is running"}

    return app
