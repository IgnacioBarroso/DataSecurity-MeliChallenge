from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.services.rag_service import ask_rag_service, debug_rag_service


router = APIRouter()


class RAGAskRequest(BaseModel):
    question: str


class RAGAskResponse(BaseModel):
    answer: str
    context_preview: str | None = None


async def ask_rag(question: str) -> dict:
    """Wrapper parcheable para tests; delega en el servicio real."""
    return await ask_rag_service(question)

@router.post("/rag/ask", response_model=RAGAskResponse, summary="Pregunta directa al RAG")
async def rag_ask(req: RAGAskRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=422, detail="La pregunta no puede estar vacía.")
    try:
        result = await ask_rag(req.question)
        return RAGAskResponse(answer=result.get("answer", ""), context_preview=result.get("context", "")[:1000])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar el RAG: {e}")


class RAGDebugResponse(BaseModel):
    question: str
    docs: list[dict]


@router.post("/rag/debug", response_model=RAGDebugResponse, summary="Debug del RAG con similitudes y selección")
async def rag_debug(req: RAGAskRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=422, detail="La pregunta no puede estar vacía.")
    try:
        docs = await debug_rag_service(req.question)
        return RAGDebugResponse(question=req.question, docs=docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al depurar el RAG: {e}")
