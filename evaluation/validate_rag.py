"""
Script de evaluación de calidad RAG usando RAGAs para el Meli Challenge.
- Define un dataset de preguntas sobre el DBIR
- Ejecuta el agente Analizador sobre cada pregunta
- Calcula métricas context_precision y faithfulness
- Imprime un reporte de evaluación
"""

import os
from ragas.metrics import context_precision, faithfulness
from ragas.evaluation import evaluate
from ragas import Dataset
from typing import List

# --- Dataset de ejemplo (puedes expandirlo) ---
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
    {
        "question": "¿Qué técnica MITRE ATT&CK se asocia frecuentemente a ataques de fuerza bruta?",
        "ground_truth": "La técnica T1110 (Brute Force) es la más asociada.",
        "expected_context": "T1110",
    },
    {
        "question": "¿Qué porcentaje de brechas involucró credenciales comprometidas?",
        "ground_truth": "Aproximadamente el 60% de las brechas involucraron credenciales comprometidas.",
        "expected_context": "credenciales",
    },
    {
        "question": "¿Qué controles recomienda el DBIR para prevenir ataques de ransomware?",
        "ground_truth": "Backups frecuentes, segmentación de red y entrenamiento de usuarios.",
        "expected_context": "backups",
    },
]


# --- Función para invocar el agente Analizador (debe adaptarse a tu código) ---
def run_threat_analyzer(question: str) -> dict:
    """
    Ejecuta el ThreatAnalyzerAgent sobre la pregunta y retorna dict con 'answer' y 'context'.
    Debes adaptar esta función a tu pipeline real.
    """
    # Ejemplo: importar tu crew y ejecutar solo el analizador
    from src.mcp_crews import SecurityAnalysisCrew

    crew = SecurityAnalysisCrew()
    result = crew.run_analysis_only(
        question
    )  # Debes implementar este método si no existe
    return result


# --- Construcción del dataset RAGAs ---
def build_ragas_dataset(eval_data: List[dict]) -> Dataset:
    questions = [item["question"] for item in eval_data]
    ground_truths = [item["ground_truth"] for item in eval_data]
    contexts = [item["expected_context"] for item in eval_data]
    # Simula outputs del sistema (debes mapear a tu output real)
    answers = []
    retrieved_contexts = []
    for item in eval_data:
        output = run_threat_analyzer(item["question"])
        answers.append(output.get("answer", ""))
        retrieved_contexts.append(output.get("context", ""))
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
