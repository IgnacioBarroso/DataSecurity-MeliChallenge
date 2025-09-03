"""
Evaluación de calidad RAG con RAGAs para el Meli Challenge.
- Usa el pipeline real de RAG (ask_rag) para obtener respuestas
- Usa el contexto devuelto por el pipeline como retrieved_contexts
"""

from typing import List
from ragas.metrics import context_precision, faithfulness
from ragas.evaluation import evaluate
from ragas import Dataset
import asyncio


# Dataset de ejemplo (modificable)
EVAL_DATA = [
    {
        "question": "¿Cuál es el vector de ataque más común reportado en el DBIR 2025?",
        "ground_truth": "El phishing sigue siendo el vector de ataque más común según el DBIR 2025.",
        "expected_context": "phishing",
    },
    {
        "question": "¿Qué sector sufrió más incidentes de ransomware?",
        "ground_truth": "El sector salud fue el más afectado por ransomware en 2025.",
        "expected_context": "salud",
    },
]


async def run_rag(question: str) -> dict:
    from src.tools.retriever import ask_rag

    return await ask_rag(question)


def build_ragas_dataset(eval_data: List[dict]) -> Dataset:
    questions = [item["question"] for item in eval_data]
    ground_truths = [item["ground_truth"] for item in eval_data]

    answers = []
    retrieved_contexts = []
    for item in eval_data:
        output = asyncio.run(run_rag(item["question"]))
        answers.append(output.get("answer", ""))
        retrieved_contexts.append(output.get("context", ""))

    # contexts de referencia opcionales (puedes dejarlo vacío si no lo tienes)
    contexts = [item.get("expected_context", "") for item in eval_data]

    return Dataset(
        questions=questions,
        ground_truths=ground_truths,
        answers=answers,
        contexts=contexts,
        retrieved_contexts=retrieved_contexts,
    )


if __name__ == "__main__":
    print("Evaluando calidad RAG con RAGAs...\n")
    dataset = build_ragas_dataset(EVAL_DATA)
    results = evaluate(dataset, metrics=[context_precision, faithfulness])
    print("\n--- Reporte de Evaluación RAG ---")
    print(results)
