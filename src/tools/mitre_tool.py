def normalize_query(query):
    # Recursively extract 'description' if present, until a string or None
    seen = set()
    while isinstance(query, dict):
        # Prevent infinite loops on malformed dicts
        id_query = id(query)
        if id_query in seen:
            break
        seen.add(id_query)
        query = query.get('description', '') or ''
    if not isinstance(query, str):
        query = str(query)
    return query
 
from crewai.tools import tool
from typing import Any
from attackcti import attack_client
from src.logging_config import logging
import json
from src.trace import get_trace_logger

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


def _mitre_attack_query_tool(query: Any) -> str:

    """
    Searches for techniques in the MITRE ATT&CK framework based on a keyword, synonym, or description.
    Useful for mapping an abstract threat vector to concrete TTPs (Tactics, Techniques, and Procedures).
    For example, if the vector is 'Credential Stuffing', this tool can find 'T1110.003 - Password Spraying'.
    """
    query = normalize_query(query)
    logger.info(f"Searching MITRE ATT&CK techniques for: '{query}'")
    tlogger = get_trace_logger()
    if tlogger:
        tlogger.info(
            "tool_invocation",
            extra={"task_name": "MITRE ATT&CK Technique Query Tool", "input_data": {"query": query}},
        )
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
                logger.warning(f"Error searching with keyword '{kw}': {e}")

        # Remove duplicates by ID preserving first occurrence
        unique_map = {}
        for tech in all_results:
            if isinstance(tech, dict) and "id" in tech and tech["id"] not in unique_map:
                unique_map[tech["id"]] = tech
        unique = unique_map.values()
        if not unique:
            logger.error(
                f"No MITRE ATT&CK techniques found for query: '{query}'."
            )
            return f"No MITRE ATT&CK techniques found for query: '{query}'."

        formatted_results = []
        for tech in list(unique)[:5]:  # Limit to the 5 most relevant results
            formatted_results.append(
                f"- ID: {tech['id']}\n"
                f"  Name: {tech['name']}\n"
                f"  Description: {tech.get('description', '').split('.')[0]}."
            )
        logger.info(f"Techniques found: {[t['id'] for t in list(unique)[:5]]}")
        if tlogger:
            tlogger.info(
                "tool_result",
                extra={
                    "task_name": "MITRE ATT&CK Technique Query Tool",
                    "output_data": "\n".join(formatted_results)[:1000],
                },
            )
        return "\n".join(formatted_results)
    except Exception as e:
        logger.error(f"An error occurred while searching MITRE ATT&CK: {e}")
        if tlogger:
            tlogger.info(
                "tool_error",
                extra={"task_name": "MITRE ATT&CK Technique Query Tool", "output_data": str(e)},
            )
        return f"An error occurred while searching MITRE ATT&CK: {e}"

mitre_attack_query_tool = tool("MITRE ATT&CK Technique Query Tool")(_mitre_attack_query_tool)


@tool("MITRE ATT&CK Technique Details Tool")
def get_mitre_technique_details(technique_id_or_name: str) -> str:
    """
    Gets full details of a specific MITRE ATT&CK technique given its ID (e.g., T1059) or name (e.g., Command and Scripting Interpreter).
    Returns a JSON with detailed information such as associated tactics, full description, and references.
    """
    try:
        client = get_attack_client()
        tech = None

        # Try to find by ID first
        if technique_id_or_name.startswith("T") and len(technique_id_or_name) >= 5:
            tech = client.get_technique_by_id(technique_id_or_name)
            # If not found, get_technique_by_id may return None

        # If not found by ID, try to find by name
        if tech is None:
            # Search by content and pick the first exact match by name
            results = client.get_techniques_by_content(technique_id_or_name)
            for r in results:
                if (
                    (isinstance(r, dict) and (
                        r.get("name", "").lower() == technique_id_or_name.lower() or
                        r.get("id", "").lower() == technique_id_or_name.lower()
                    ))
                ):
                    tech = r
                    break

        if tech is None:
            logging.warning(
                f"No details found for MITRE ATT&CK technique: '{technique_id_or_name}'."
            )
            return f"No details found for MITRE ATT&CK technique: '{technique_id_or_name}'."

        details = {
            "id": tech["id"],
            "name": tech["name"],
            "description": tech.get("description", ""),
            "tactics": [t["name"] for t in tech.get("tactics", [])] if tech.get("tactics") else [],
            "platforms": tech.get("platforms", []),
            "data_sources": tech.get("data_sources", []),
            "detection": tech.get("detection", "No detection guidance available."),
            "references": [ref["url"] for ref in tech.get("references", [])] if tech.get("references") else [],
        }
        out = json.dumps(details, indent=2)
        tlogger = get_trace_logger()
        if tlogger:
            tlogger.info(
                "tool_result",
                extra={
                    "task_name": "MITRE ATT&CK Technique Details Tool",
                    "output_data": out[:1000],
                },
            )
        return out

    except Exception as e:
        logging.error(
            f"An error occurred while getting MITRE ATT&CK technique details: {e}"
        )
        tlogger = get_trace_logger()
        if tlogger:
            tlogger.info(
                "tool_error",
                extra={
                    "task_name": "MITRE ATT&CK Technique Details Tool",
                    "output_data": str(e),
                },
            )
        return (
            f"An error occurred while getting MITRE ATT&CK technique details: {e}"
        )
