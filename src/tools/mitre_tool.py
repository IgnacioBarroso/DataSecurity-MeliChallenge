# Fake para mocking en tests
attack = None
from crewai.tools import tool
from attackcti import attack_client
from src.logging_config import logging
import json

# Inicializa el cliente para la API de MITRE ATT&CK.
_attack = None


def get_attack_client():
    global _attack
    if _attack is None:
        _attack = attack_client()
    return _attack


# Logger específico para la herramienta
logger = logging.getLogger(__name__)


def _generate_keywords(query: str) -> list:
    # Hook para integración futura de LLM para generar keywords más efectivas
    # Por ahora, solo retorna la query original y su lower
    return [query, query.lower()]


@tool("MITRE ATT&CK Technique Query Tool")
def mitre_attack_query_tool(query: str) -> str:
    """
    Busca técnicas en el framework MITRE ATT&CK basadas en una palabra clave, sinónimo o descripción.
    Es útil para mapear un vector de amenaza abstracto a TTPs (Tácticas, Técnicas y Procedimientos) concretos.
    Por ejemplo, si el vector es 'Credential Stuffing', esta herramienta puede encontrar 'T1110.003 - Password Spraying'.
    """
    logger.info(f"Buscando técnicas MITRE ATT&CK para: '{query}'")
    try:
        client = get_attack_client()
        keywords = _generate_keywords(query)
        all_results = []
        for kw in keywords:
            try:
                results = client.get_techniques_by_content(kw)
                if results:
                    all_results.extend(results)
            except Exception as e:
                logger.warning(f"Error buscando con keyword '{kw}': {e}")
        # Eliminar duplicados por ID
        unique = {tech.id: tech for tech in all_results}.values()
        if not unique:
            logger.error(
                f"No se encontraron técnicas de MITRE ATT&CK para la consulta: '{query}'."
            )
            return f"No se encontraron técnicas de MITRE ATT&CK para la consulta: '{query}'."

        formatted_results = []
        for tech in list(unique)[:5]:  # Limita a los 5 resultados más relevantes
            formatted_results.append(
                f"- ID: {tech.id}\n"
                f"  Nombre: {tech.name}\n"
                f"  Descripción: {tech.description.split('.')[0]}."
            )
        logger.info(f"Técnicas encontradas: {[t.id for t in list(unique)[:5]]}")
        return "\n".join(formatted_results)
    except Exception as e:
        logger.error(f"Ocurrió un error al buscar en MITRE ATT&CK: {e}")
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
        if technique_id_or_name.startswith("T") and len(technique_id_or_name) >= 5:
            tech = client.get_technique_by_id(technique_id_or_name)

        # If not found by ID, try to find by name
        if tech is None:
            # Search by content and pick the first exact match by name
            results = client.get_techniques_by_content(technique_id_or_name)
            for r in results:
                if (
                    r.name.lower() == technique_id_or_name.lower()
                    or r.id.lower() == technique_id_or_name.lower()
                ):
                    tech = r
                    break

        if tech is None:
            logging.warning(
                f"No se encontraron detalles para la técnica de MITRE ATT&CK: '{technique_id_or_name}'."
            )
            return f"No se encontraron detalles para la técnica de MITRE ATT&CK: '{technique_id_or_name}'."

        details = {
            "id": tech.id,
            "name": tech.name,
            "description": tech.description,
            "tactics": [t.name for t in tech.tactics] if tech.tactics else [],
            "platforms": tech.platforms if tech.platforms else [],
            "data_sources": tech.data_sources if tech.data_sources else [],
            "detection": (
                tech.detection if tech.detection else "No detection guidance available."
            ),
            "references": (
                [ref.url for ref in tech.references] if tech.references else []
            ),
        }
        return json.dumps(details, indent=2)

    except Exception as e:
        logging.error(
            f"Ocurrió un error al obtener detalles de la técnica de MITRE ATT&CK: {e}"
        )
        return (
            f"Ocurrió un error al obtener detalles de la técnica de MITRE ATT&CK: {e}"
        )
