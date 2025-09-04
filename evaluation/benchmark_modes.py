import os
import json
import time
import subprocess

SAMPLE_QUESTIONS = [
    "¿Cuál es un vector de ataque común según el DBIR 2025?",
    "¿Qué riesgos clave hay con APIs expuestas en un hub de pagos?",
]


def run_cli(mode: str, question: str) -> float:
    env = os.environ.copy()
    env["ANALYZER_MODE"] = mode
    t0 = time.perf_counter()
    out = subprocess.run([
        "poetry", "run", "python", "main.py", "rag", question
    ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    dt = (time.perf_counter() - t0) * 1000.0
    return dt


def main():
    results = {"heavy": [], "turbo": []}
    for q in SAMPLE_QUESTIONS:
        for mode in ("heavy", "turbo"):
            ms = run_cli(mode, q)
            results[mode].append(ms)
            print(f"{mode.upper()} - '{q[:30]}...': {ms:.1f} ms")
    summary = {
        m: {
            "count": len(results[m]),
            "avg_ms": sum(results[m]) / max(1, len(results[m])),
            "min_ms": min(results[m]) if results[m] else None,
            "max_ms": max(results[m]) if results[m] else None,
        }
        for m in results
    }
    print("\nSummary:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

