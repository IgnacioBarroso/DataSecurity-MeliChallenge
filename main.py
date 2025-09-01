# main.py
import argparse
import sys
import logging
from api.services import crew_service
from src.config import load_config

# Cargar configuración (necesario para el llm_provider)
load_config()

def main_cli():
    """Punto de entrada para ejecutar el análisis desde la línea de comandos."""
    parser = argparse.ArgumentParser(
        description="DataSec AI Agent CLI - Herramienta para analizar el contexto de una aplicación desde un archivo."
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Ruta al archivo de texto (.txt) que contiene la descripción de la aplicación a analizar."
    )
    args = parser.parse_args()

    print(f"--- Iniciando Análisis desde CLI para el archivo: {args.input_file} ---")
    
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            user_input_text = f.read()
    except FileNotFoundError:
        print(f"ERROR: El archivo de entrada no fue encontrado en '{args.input_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: No se pudo leer el archivo de entrada: {e}")
        sys.exit(1)

    try:
        print("Ejecutando el pipeline de agentes... Esto puede tardar varios minutos.")
        # Llamar directamente a la función del servicio
        report = crew_service.run_security_analysis(user_input_text)
        
        print("\n--- ✅ ANÁLISIS COMPLETADO EXITOSAMENTE ---")
        print(f"\nReporte ID (y archivo de log): {report.report_id}")
        print(f"Aplicación Analizada: {report.application_name}")
        print(f"\nResumen: {report.summary}")
        
        print("\n--- Detectores Priorizados ---")
        for detector in sorted(report.prioritized_detectors, key=lambda d: d.priority):
            print(f"\n{detector.priority}. {detector.detector_name} [Riesgo: {detector.risk_level}]")
            print(f"   Justificación: {detector.rationale[:100]}...")
        
        print("\nPara ver el detalle completo, revisa el archivo de log en la carpeta /logs.")

    except Exception as e:
        print(f"\n--- ❌ ERROR DURANTE EL ANÁLISIS ---")
        logging.error(f"La ejecución del crew falló: {e}", exc_info=True)
        print("Ocurrió un error crítico. Revisa el log de la consola para más detalles.")
        sys.exit(1)

if __name__ == "__main__":
    main_cli()