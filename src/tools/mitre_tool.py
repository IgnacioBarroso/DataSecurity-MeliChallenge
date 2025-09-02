from crewai.tools import tool
from attackcti import attack_client
import logging
import json

# Inicializa el cliente para la API de MITRE ATT&CK.
# Esto se hace una sola vez cuando el módulo es importado.
attack = None

def get_attack_client():
    global attack
    if attack is None:
        attack = attack_client()
    return attack

@tool("MITRE ATT&CK Technique Query Tool")
def mitre_attack_query_tool(query: str) -> str:
    """
    Busca técnicas en el framework MITRE ATT&CK basadas en una palabra clave o frase.
    Es útil para mapear un vector de amenaza abstracto a TTPs (Tácticas, Técnicas y Procedimientos) concretos.
    Por ejemplo, si el vector es 'Credential Stuffing', esta herramienta puede encontrar 'T1110.003 - Password Spraying'.
    """
    try:
        results = get_attack_client().get_techniques_by_content(query, case_sensitive=False)
        
        if not results:
            logging.error(f"No se encontraron técnicas de MITRE ATT&CK para la consulta: '{query}'.")
            return f"No se encontraron técnicas de MITRE ATT&CK para la consulta: '{query}'."

        formatted_results = []
        for tech in results[:5]: # Limita a los 5 resultados más relevantes para brevedad.
            formatted_results.append(
                f"- ID: {tech.id}\n"
                f"  Nombre: {tech.name}\n"
                f"  Descripción: {tech.description.split('.')[0]}."
            )
        
        return "\n".join(formatted_results)
    except Exception as e:
        logging.error(f"Ocurrió un error al buscar en MITRE ATT&CK: {e}")
        return f"Ocurrió un error al buscar en MITRE ATT&CK: {e}"

@tool("MITRE ATT&CK Technique Details Tool")
def get_mitre_technique_details(technique_id_or_name: str) -> str:
    """
    Obtiene detalles completos de una técnica específica de MITRE ATT&CK dado su ID (ej. T1059) o nombre (ej. Command and Scripting Interpreter).
    Retorna un JSON con información detallada como tácticas asociadas, descripción completa, y referencias.
    """
    try:
        client = get_attack_client()
        tech = None

        # Try to find by ID first
        if technique_id_or_name.startswith('T') and len(technique_id_or_name) >= 5:
            tech = client.get_technique(technique_id_or_name)
        
        # If not found by ID, try to find by name
        if tech is None:
            # Search by content and pick the first exact match by name
            results = client.get_techniques_by_content(technique_id_or_name, case_sensitive=False)
            for r in results:
                if r.name.lower() == technique_id_or_name.lower() or r.id.lower() == technique_id_or_name.lower():
                    tech = r
                    break

        if tech is None:
            logging.warning(f"No se encontraron detalles para la técnica de MITRE ATT&CK: '{technique_id_or_name}'.")
            return f"No se encontraron detalles para la técnica de MITRE ATT&CK: '{technique_id_or_name}'."

        details = {
            "id": tech.id,
            "name": tech.name,
            "description": tech.description,
            "tactics": [t.name for t in tech.tactics] if tech.tactics else [],
            "platforms": tech.platforms if tech.platforms else [],
            "data_sources": tech.data_sources if tech.data_sources else [],
            "detection": tech.detection if tech.detection else "No detection guidance available.",
            "references": [ref.url for ref in tech.references] if tech.references else []
        }
        return json.dumps(details, indent=2)

    except Exception as e:
        logging.error(f"Ocurrió un error al obtener detalles de la técnica de MITRE ATT&CK: {e}")
        return f"Ocurrió un error al obtener detalles de la técnica de MITRE ATT&CK: {e}"