import argparse
import sys
from src.mcp_crews import SecurityAnalysisCrew
import logging
from src.logging_config import setup_agent_trace_logging
from src.tools.retriever import ask_rag


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
        import asyncio
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
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report if isinstance(report, str) else str(report))
            print(f"Reporte guardado en {args.output}")
        else:
            print("\n--- REPORTE DE SEGURIDAD ---\n")
            print(report)


if __name__ == "__main__":
    main()
