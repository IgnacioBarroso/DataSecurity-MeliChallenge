# **Desafío DataSec Challenge**

**mercado libre**

El equipo de Data Security de Mercado Libre, se encarga de securizar las aplicaciones internas en Meli, dichas aplicaciones son utilizadas por colaboradores internos para diferentes fines. Uno de los mayores desafíos de este equipo es poder determinar si un usuario realiza acciones anómalas o indebidas sobre dichas aplicaciones y generar de forma ágil mecanismos detectivos que permitan evitar dicha actividad a tiempo.

Estamos investigando si la IA podría agilizar la creación y actualización de los mecanismos detectivos, para esto nos pidieron que desarrollaramos un sistema multiagente, el cual pueda llevar de punta a punta un análisis de vectores de ataques reales sin necesidad concreta de interacción con un analista de seguridad.

Aunque la gestión de estos hallazgos y la creación de mecanismos de seguridad en un marco corporativo es diferente, nos interesa identificar si esta tecnología es viable para realizar estas tareas de forma autónoma y luego escalarla en un flujo más complejo.

## **Objetivo**

Realizar un sistema multiagente que posea las características mencionadas a continuación y pueda realizar las tareas propuestas para la creación de nuevos mecanismos detectivos:

**Sistema:** La solución debe ser una arquitectura multiagente compuesta por 3 agentes específicos que implementen un pipeline secuencial de análisis de vectores de ataque/riesgos, comparativa con el contexto del ecosistema a evaluar, y generación de un reporte de detectores prioritarios.

Este sistema debe tomar como dato el informe "Data Breach Investigations Report 2025" el cual será la base para comparar e identificar necesidades de implementación.

**Tareas del flujo de agentes:**

**Comparativa entre contexto y datos de reporte/s:**

* Se debe poder tomar input estructurado del usuario sobre su ecosistema (se proporcionará template específico). Este input será un texto descriptivo sobre aplicaciones web internas corporativas.  
* El sistema deberá procesar esta información junto con el subset del reporte para identificar hasta 5 detectores prioritarios a desarrollar, categorizados en Alto/Medio/Bajo riesgo.

**Análisis de riesgos:**

* El sistema deberá asociar cada detector identificado a técnicas específicas del framework "MITRE ATT\&CK techniques" utilizando un MCP existente.  
* Mediante dicha asociación, el sistema deberá poder clasificarlos riesgos en 3 categorías (Alto/Medio/Bajo impacto) y los priorizará para el reporte final.

**Generación del reporte:**

* Se deberá generar un reporte que no solo contenga de forma clara los detectores propuestos, el análisis de riesgos y el racional detrás de cada caso sino que también una propuesta de accionables indicando los pasos a tomar para el/los equipos de seguridad que queramos involucrar en el desarrollo de estos detectores.

**Características necesarias:**

* Diferentes agentes deberán tener roles y responsabilidades específicas en un flujo secuencial con puntos de validación:  
  * **Agente Analizador:** Procesa el input del usuario y lo compara con el subset del reporte.  
  * **Agente Clasificador:** Mapea los hallazgos a técnicas MITRE ATT\&CK y asigna niveles de riesgo.  
  * **Agente Reporting:** Genera el reporte final con recomendaciones.  
* Incluir manejo de errores para interacciones fallidas y validación de datos entre agentes.  
* **Creación de MCP/s para agentes:** Desarrollar o utilizar al menos 1 MCPs (Model Context Protocols) existentes para gestionar/otorgar múltiples herramientas a los agentes del sistema para las tareas necesarias de cada rol.  
  * Al menos 1 MCP es requerido, se permite utilizar MCP desarrollados por la comunidad:  
    * Ej: https://github.com/search?q=mitre-attack-mcp\&type=repositories.

**Entregables**

* Generar registros de input-output de cada agente para poder validar los pasos intermedios en todo momento y tener trazabilidad de las interacciones/decisiones, esto puede estar en un formato a elección pero debe generarse en un almacenamiento centralizado con cada ejecución con identificadores que permitan recrear el flujo de una "sesión".  
* Reporte de seguridad final que los agentes generen (pueden incluir varios ejemplos).  
* Informe de cualquier otros supuestos, comentarios, observaciones del análisis, problemas y soluciones con los que se encontró al realizar este challenge.  
* Dockerizar la solución y entregarla.

## **Bonus**

Estos puntos no son estrictamente necesarios pero tomaremos su implementación como un "plus" en la entrega, están ordenados por prioridad:

1. Implementar un modelo local que garantice resultados similares.  
2. Disponibilizar la app en un frontend.  
3. Generar un mecanismo para validar la calidad de los datos recuperados por los métodos de RAG.  
4. Realizar un benchmark entre modelos, prompts o de las representaciones vectoriales (embeddings).  
5. Generar lógica de versiones en configuraciones/prompts utilizado por los agentes.

## **Consideraciones importantes**

A tener en cuenta:

* **La solución debe ser de fácil ejecución por lo tanto deben detallarse las dependencias o ser solucionada la instalación de las mismas en otro entorno mediante su inclusión en el código. (En caso de no Dockerizar)**  
* Se podrán crear todas las funciones complementarias que se consideren necesarias para procesar/transformar la información.  
* El "input" no será dado para este challenge ya que será la forma de evaluar el sistema, se espera que el candidato modele una serie de inputs a fin de probar su solución antes de la entrega.

**Ejemplos de input para candidatos**

¡Gracias por tu interés en sumarte a nuestro equipo\!

Cuando finalices, te pedimos que nos envíes tu resolución y luego agendaremos un espacio de 30' para que, junto con la presentación de tu análisis, puedas ampliar:

* Qué decisiones tomaste al construir tu desafío.  
* Otros puntos que consideres importantes.

¡Manos a la obra\!