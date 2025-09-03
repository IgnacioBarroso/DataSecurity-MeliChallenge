import argparse
import asyncio
import json
import logging
import sys
import api.auto_dotenv  # Carga variables de entorno desde .env para CLI
from src.mcp_crews import SecurityAnalysisCrew
from src.logging_config import setup_agent_trace_logging
from src.tools.retriever import ask_rag
try:
    from pydantic import BaseModel  # type: ignore
except Exception:
    BaseModel = object


def main():
    parser = argparse.ArgumentParser(description="CLI para ejecutar el análisis de seguridad MCP.")
    sub = parser.add_subparsers(dest="cmd", required=False)

    # Subcomando: análisis desde archivo
    p_analyze = sub.add_parser("analyze", help="Analiza un archivo de texto de entrada")
    p_analyze.add_argument("input_file", type=str, help="Ruta al archivo de texto a analizar.")
    p_analyze.add_argument("--output", type=str, default=None, help="Ruta para guardar el reporte (opcional).")

    # Subcomando: pregunta directa al RAG
    p_rag = sub.add_parser("rag", help="Pregunta directa al RAG del DBIR")
    p_rag.add_argument("question", type=str, help="Pregunta a realizar al RAG.")
    args = parser.parse_args()

    if args.cmd == "rag":
        print("Consultando RAG...")
        result = asyncio.run(ask_rag(args.question))
        print("\n--- RESPUESTA RAG ---\n")
        print(result.get("answer", ""))
        print("\n--- CONTEXTO (preview) ---\n")
        print(result.get("context", "")[:1000])
        return

    # Default: analyze
    if not args.cmd or args.cmd == "analyze":
        try:
            with open(args.input_file, "r", encoding="utf-8") as f:
                user_input = f.read()
        except Exception as e:
            print(f"Error al leer el archivo: {e}")
            sys.exit(1)

        print("Ejecutando SecurityAnalysisCrew...")
        session_id = "cli-" + str(abs(hash(args.input_file)))
        logger = setup_agent_trace_logging(session_id)
        crew = SecurityAnalysisCrew(agent_trace_logger=logger)
        report = crew.run(user_input)

        if hasattr(args, "output") and args.output:
            # Normalizar a JSON estricto
            out_str = None
            try:
                if isinstance(report, BaseModel):
                    out_str = report.model_dump_json()
            except Exception:
                pass
            if out_str is None and isinstance(report, dict):
                out_str = json.dumps(report, ensure_ascii=False)
            if out_str is None and isinstance(report, str):
                try:
                    obj = json.loads(report)
                    if isinstance(obj, dict) and "raw" in obj and isinstance(obj["raw"], str):
                        data = json.loads(obj["raw"])
                        out_str = json.dumps(data, ensure_ascii=False)
                    else:
                        out_str = report
                except Exception:
                    out_str = report
            if out_str is None:
                s = str(report)
                try:
                    obj = json.loads(s)
                    if isinstance(obj, dict) and "raw" in obj and isinstance(obj["raw"], str):
                        data = json.loads(obj["raw"])
                        out_str = json.dumps(data, ensure_ascii=False)
                    else:
                        out_str = s
                except Exception:
                    out_str = s

            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out_str)
            print(f"Reporte guardado en {args.output}")
        else:
            print("\n--- REPORTE DE SEGURIDAD ---\n")
            print(report)


if __name__ == "__main__":
    main()
