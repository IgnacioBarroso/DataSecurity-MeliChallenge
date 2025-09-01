from crewai.tools import tool
from attackcti import attack_client

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
        # Realiza la búsqueda de técnicas que coincidan con la consulta.
        # get_techniques_by_content busca la consulta en nombres, descripciones, etc.
        results = get_attack_client().get_techniques_by_content(query, case_sensitive=False)
        
        if not results:
            return f"No se encontraron técnicas de MITRE ATT&CK para la consulta: '{query}'."

        # Formatea los resultados para que sean fáciles de procesar por el LLM.
        formatted_results = []
        for tech in results[:5]: # Limita a los 5 resultados más relevantes para brevedad.
            formatted_results.append(
                f"- ID: {tech.id}\n"
                f"  Nombre: {tech.name}\n"
                f"  Descripción: {tech.description.split('.')[0]}." # Solo la primera oración.
            )
        
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Ocurrió un error al buscar en MITRE ATT&CK: {e}"