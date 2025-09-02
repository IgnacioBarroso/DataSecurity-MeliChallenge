# **Plan de Acción Estratégico para Finalizar el Meli Challenge**

## **1. Introducción y Objetivo**

Este documento es una guía estratégica y técnica para refactorizar y finalizar el proyecto "Meli Challenge". El objetivo principal es alinear la solución actual con la **arquitectura MCP (Model Context Protocol) de 3 agentes** solicitada explícitamente en el desafío, eliminando el código residual de la arquitectura agentica anterior de 5 agentes, y asegurando que todos los requisitos funcionales y "plus" se cumplan de manera robusta y eficiente.

Seguiremos un enfoque estructurado, modificando sección por sección el código base para garantizar la coherencia y la calidad del producto final.

## **2. Refactorización del Núcleo: Arquitectura de 3 Agentes (MCP)**

**Objetivo:** Simplificar la arquitectura actual de 5 agentes a la arquitectura de 3 agentes requerida: **Analizador**, **Clasificador** y **Reporte**. Esto implica consolidar responsabilidades y redefinir el flujo de trabajo.


## **10. Correcciones Finales para Robustez y Tests**

**Objetivo:** Ajustar detalles de integración, mocks, dependencias y validaciones para asegurar que todos los tests pasen y la solución sea robusta y mantenible.

### **⬜ Checklist de Correcciones**

* [ ] **Exponer y/o crear los mocks/fakes necesarios en los módulos para que los tests puedan mockear correctamente:**
  * [ ] Exponer `run_mcp_analysis` y `setup_agent_trace_logging` en `api/services/crew_service.py` si los tests lo requieren.
* [ ] **Alinear los nombres de modelos/configuración para que los tests de LLM pasen:**
  * [ ] Ajustar el valor por defecto y mocks de `OPENAI_MODEL_NAME` a `gpt-4.1-nano` en los tests y/o código si es necesario.
* [ ] **Corregir detalles de validación y logs para que los tests sean robustos:**
  * [ ] Asegurar que los endpoints y modelos acepten el input esperado por los tests (`user_input` vs `text`).
  * [ ] Ajustar los mensajes de error y logs para que coincidan con lo que esperan los asserts de los tests.
* [ ] **Mocks y dependencias de herramientas:**
  * [ ] Exponer o crear los atributos/fakes (`attack`, `query_dbir_report`) en los módulos de herramientas para que los tests puedan mockearlos.
* [ ] **Configurar correctamente las variables de entorno de test:**
* [ ] **Revisar y ajustar los tests para que sean consistentes con la arquitectura y modelos actuales:**
  * [ ] Modificar los tests que dependan de detalles internos obsoletos o que no reflejen el flujo MCP actual.

---

* [x] **Modificar src/agents.py:**  
  * [x] Eliminar las clases InputParsingAgent, RAGQualityValidator y sus prompts asociados.  
  * [x] Renombrar y/o redefinir las clases restantes para que se correspondan con los 3 agentes requeridos:  
   1. **ThreatAnalyzerAgent (Agente Analizador):**  
     * **Responsabilidad:** Recibir el input del usuario, analizarlo para identificar debilidades y usar la herramienta RAG para encontrar amenazas relevantes en el DBIR. Su output debe ser una lista estructurada de hallazgos iniciales.  
     * **Herramienta principal:** DBIRRAGTool.  
   2. **RiskClassifierAgent (Agente Clasificador):**  
     * **Responsabilidad:** Tomar los hallazgos del analizador y enriquecerlos usando la herramienta de MITRE ATT\&CK para mapear cada riesgo a TTPs (Tácticas, Técnicas y Procedimientos) específicos.  
     * **Herramienta principal:** MitreAttackTool.  
   3. **ReportingAgent (Agente de Reporte):**  
     * **Responsabilidad:** Recibir los datos enriquecidos del clasificador y generar el reporte final en formato Markdown, incluyendo accionables técnicos y claros.  
     * **Herramientas:** Ninguna herramienta externa, solo capacidad de generación de texto.  
* [x] **Modificar src/mcp_crews.py:**  
  * [x] Renombrar la clase MeliChallengeCrew a SecurityAnalysisCrew o similar.  
  * [x] Eliminar la instanciación de los agentes InputParsingAgent y RAGQualityValidator.  
  * [x] Reconstruir la Crew para que contenga únicamente los 3 nuevos agentes.  
  * [x] Definir las tareas (tasks) para un flujo estrictamente secuencial:  
    1. analysis_task: Ejecutada por el ThreatAnalyzerAgent.  
    2. classification_task: Ejecutada por el RiskClassifierAgent, tomando como contexto (context) el output de analysis_task.  
    3. reporting_task: Ejecutada por el ReportingAgent, tomando como contexto (context) el output de classification_task.  
  * [x] Asegurarse de que la Crew se inicialice con process=Process.sequential.  
* [x] **Actualizar src/models.py (Modelos Pydantic):**  
  * [x] Eliminar modelos Pydantic que ya no sean necesarios (ej. ParsedInput).  
  * [x] Definir modelos de datos claros para el intercambio de información entre los 3 agentes. Sugerencia:  
    * ThreatFinding: Un modelo para el output del Analizador (ej. detector_name: str, risk_description: str, initial_severity: str).  
    * EnrichedFinding: Un modelo para el output del Clasificador, que herede de ThreatFinding y añada el mapeo a MITRE (ej. mitre_ttps: List[dict]).  
    * FinalReport: Un modelo que encapsule el resultado final.  
  * [x] Forzar el output de los agentes Analizador y Clasificador para que usen estos modelos Pydantic, usando el parámetro output_json o output_pydantic en sus tareas.

## **3. Configuración y Gestión de LLMs**

**Objetivo:** Refinar el sistema de selección de LLMs para que sea robusto, claro y cumpla con el requisito de fácil switcheo entre un modelo cloud (OpenAI) y uno local (Ollama).

### **✅ Checklist de Acciones**

* [x] **Revisar src/llm_provider.py:**  
  * [x] Simplificar la lógica. La función get_llm debe leer una única variable de entorno, LLM_PROVIDER (openai o ollama), y en base a eso, instanciar el cliente correspondiente.  
  * [x] En la sección de OpenAI, asegúrate de que el model_name se cargue desde una variable de entorno (ej. OPENAI_MODEL_NAME) para no dejarlo hardcodeado. Utiliza gpt-4.1-nano como valor por defecto en el .env.example, ya que es uno de los modelos a los que tienes acceso.  
  * [x] De manera similar, para los embeddings, usa text-embedding-3-small.  
  * [x] Añadir comentarios claros que expliquen cómo funciona la selección.  
* [x] **Actualizar .env y .env.example:**  
  * [x] Limpiar variables no utilizadas.  
  * [x] Dejar una estructura clara:  
    # GENERAL  
    LLM_PROVIDER="openai" # Cambiar a "ollama" para usar modelo local

    # --- OPENAI CONFIG ---  
    OPENAI_API_KEY="tu_api_key"  
    OPENAI_MODEL_NAME="gpt-4.1-nano"  
    OPENAI_EMBEDDING_MODEL="text-embedding-3-small"

    # --- OLLAMA CONFIG ---  
    OLLAMA_BASE_URL="http://localhost:11434" # Usar http://host.docker.internal:11434 si se ejecuta desde Docker  
    OLLAMA_MODEL="llama3"

## **4. Mejora de Herramientas (Tools)**

**Objetivo:** Incrementar la calidad y robustez de las herramientas que utilizan los agentes, especialmente el sistema RAG.

### **✅ Checklist de Acciones**

* [x] **Implementar Re-ranking en src/tools/dbir_rag_tool.py (RAG Avanzado):**  
  * [x] El desafío valora la calidad del RAG. Una mejora significativa es añadir un "re-ranker".  
  * [x] Modificar la herramienta para que, después de obtener los documentos iniciales de ChromaDB, utilice un CrossEncoder de langchain_community.cross_encoders para reordenarlos por relevancia antes de pasarlos al LLM.  
  * [x] Puedes usar un modelo como mixedbread-ai/mxbai-rerank-xsmall-v1 que es ligero y efectivo.  
  * [x] Añadir sentence-transformers a pyproject.toml.  
* [x] **Reforzar src/tools/mitre_tool.py:**  
  * [x] Añadir manejo de errores. ¿Qué pasa si la librería attackcti no encuentra una técnica para una búsqueda dada? La herramienta debe devolver un mensaje claro en lugar de fallar.  
  * [x] Asegurarse de que la función de búsqueda sea lo suficientemente flexible para manejar sinónimos o descripciones de riesgo (ej. "fuerza bruta" debería mapear a T1110). Puedes usar un LLM dentro de la propia herramienta para generar keywords de búsqueda más efectivas.  
* [x] **Añadir Logging a las Herramientas:**  
  * [x] Utilizar el logging_config.py para instanciar un logger en cada archivo de herramienta (logger = logging.getLogger(__name__)).  
  * [x] Registrar los inputs y outputs de cada ejecución de la herramienta. Ejemplo en DBIRRAGTool: logger.info(f"Buscando en DBIR con query: '{query}'") y logger.info("Documentos recuperados: ..."). Esto es **crucial** para la trazabilidad requerida.

## **5. Ajustes en la API y CLI**

**Objetivo:** Asegurar que la API de FastAPI y el punto de entrada main.py (CLI) reflejen la nueva arquitectura y sean fáciles de usar.

### **✅ Checklist de Acciones**

* [x] **Revisar api/:**  
  * [x] Actualizar el schema en api/schemas/analysis.py para que el AnalysisRequest solo pida el user_input: str.  
  * [x] El AnalysisResponse debe devolver el report: str (el Markdown final) y quizás un session_id para el logging.  
  * [x] Simplificar api/services/crew_service.py para que solo cree una instancia de la SecurityAnalysisCrew y ejecute el proceso.  
  * [x] Asegurarse de que el router en api/routers/analysis.py esté usando los schemas correctos.  
* [x] **Revisar main.py (CLI):**  
  * [x] Simplificar el script para que tome la ruta a un archivo de texto como argumento.  
  * [x] Instancie y ejecute la SecurityAnalysisCrew.  
  * [x] Imprima el reporte final en la consola y, opcionalmente, lo guarde en un archivo en una carpeta reports/.

## **6. Actualización de la Suite de Pruebas**

**Objetivo:** Adecuar todos los tests a la nueva arquitectura de 3 agentes, asegurando una cobertura de código alta y la fiabilidad de la aplicación.

### **✅ Checklist de Acciones**

* [x] **Eliminar/Refactorizar Tests Obsoletos:**  
  * [x] Eliminar tests/test_parsing_agent.py y tests/test_parsing_agent_extra.py.  
  * [x] Revisar tests/test_crew.py y tests/test_e2e_analysis.py para que reflejen el nuevo flujo de 3 tareas.  
* [x] **Crear Nuevos Tests Unitarios:**  
  * [x] Crear tests para cada una de las herramientas en tests/test_tools.py, mockeando las llamadas externas (a ChromaDB o al LLM) para probar la lógica de re-ranking y el manejo de errores.  
* [x] **Tests de Integración:**  
  * [x] En tests/test_crew.py, crear un test de integración que ejecute la Crew completa con un LLM mockeado (mocker.patch) para verificar que el output de una tarea se pasa correctamente como input a la siguiente.  
* [x] **Tests E2E:**  
  * [x] En tests/test_api.py, mantener y reforzar los tests que llaman al endpoint /analysis y verifican que la respuesta sea un reporte en Markdown bien formado.

## **7. Dockerización y Entorno de Ejecución**

**Objetivo:** Facilitar al máximo la ejecución del proyecto, cumpliendo con uno de los requisitos más importantes del challenge.

### **✅ Checklist de Acciones**

* [x] **Optimizar Dockerfile:**  
  * [x] Utilizar un Dockerfile multi-etapa para reducir el tamaño final de la imagen. Una etapa para instalar dependencias y otra para copiar la aplicación.  
* [x] **Mejorar docker-compose.yml:**  
  * [x] Añadir un servicio para Ollama, de modo que se pueda levantar todo el entorno local con un solo comando.  
    services:  
      api:  
        # ... tu configuración actual  
      ollama:  
        image: ollama/ollama  
        ports:  
          - "11434:11434"  
        volumes:  
          - ollama_data:/root/.ollama  
    volumes:  
      ollama_data:

  * [x] Con esto, la OLLAMA_BASE_URL en el .env para Docker debería ser http://ollama:11434.

## **8. Implementación de Puntos Extra ("Plus" Features)**

**Objetivo:** Abordar los puntos extra de mayor prioridad para destacar la solución.

### **✅ Checklist de Acciones**

* [ ] **(Plus 1) Modelo Local:** Ya cubierto con la integración de Ollama y Docker Compose.  
* [x] **(Plus 2) Frontend:**  
  * [x] El frontend/index.html es un buen inicio. Se puede mejorar con un fetch de JavaScript simple que llame al endpoint de la API y muestre el reporte en la página sin recargar. Es un cambio menor pero de gran impacto visual.  
* [x] **(Plus 3) Validación de Calidad de RAG:**  
  * [x] Crear una nueva carpeta evaluation/.  
  * [x] Dentro, crear un script validate_rag.py que utilice el framework **RAGAs**.  
  * [x] Este script debería:  
    1. Definir un pequeño "dataset de evaluación" (5-10 preguntas sobre el DBIR con respuestas y contextos esperados).  
    2. Ejecutar el sistema RAG (solo el Agente Analizador) sobre estas preguntas.  
    3. Usar RAGAs para calcular métricas como context_precision y faithfulness.  
    4. Imprimir un reporte de evaluación.  
  * [x] Añadir ragas a las dependencias de desarrollo en pyproject.toml.  
  * [x] Documentar cómo ejecutar esta evaluación en el README.md.

## **9. Verificación Final y Documentación**

**Objetivo:** Pulir el proyecto para la entrega, asegurando que toda la documentación esté actualizada y sea clara.

### **✅ Checklist de Acciones**

* [x] **Actualizar README.md:**  
  * [x] Reescribir la sección de "Arquitectura" para describir el nuevo flujo de 3 agentes.  
  * [x] Actualizar las instrucciones de ejecución para reflejar los cambios en Docker Compose y el .env.  
  * [x] Añadir una sección sobre cómo ejecutar los tests y la evaluación de RAG.  
* [x] **Limpiar el Código:**  
  * [x] Ejecutar black y flake8 (o las herramientas de linting que prefieras) para asegurar un formato de código consistente.  
  * [x] Eliminar archivos no utilizados (ej. __pycache__ del control de versiones, ya está en .gitignore pero revisar por si acaso).  
* [x] **Revisar ENTREGA_CHECKLIST.md:**  
  * [x] Marcar todos los puntos completados, asegurándose de que cada requisito del challenge original ha sido abordado.