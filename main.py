import argparse
import sys
from src.mcp_crews import SecurityAnalysisCrew


def main():
    parser = argparse.ArgumentParser(
        description="CLI para ejecutar el análisis de seguridad MCP."
    )
    parser.add_argument(
        "input_file", type=str, help="Ruta al archivo de texto a analizar."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Ruta para guardar el reporte Markdown (opcional).",
    )
    args = parser.parse_args()

    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            user_input = f.read()
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        sys.exit(1)

    print("Ejecutando SecurityAnalysisCrew...")
    crew = SecurityAnalysisCrew()
    report = crew.run(user_input)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Reporte guardado en {args.output}")
    else:
        print("\n--- REPORTE DE SEGURIDAD ---\n")
        print(report)


if __name__ == "__main__":
    main()
