from __future__ import annotations

from typing import Dict, List
from src.tools.retriever import ask_rag, get_docs_with_scores


async def ask_rag_service(question: str) -> Dict:
    return await ask_rag(question)


async def debug_rag_service(question: str) -> List[Dict]:
    return await get_docs_with_scores(question)

