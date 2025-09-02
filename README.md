# Sistema Multiagente Autónomo para la Detección de Amenazas

## 1. Descripción General del Proyecto

Este proyecto es una implementación del "DataSec Challenge" de Mercado Libre. El objetivo es desarrollar un sistema multiagente autónomo que utiliza IA para analizar inteligencia de amenazas (basada en el Verizon DBIR 2025) en el contexto de una aplicación interna específica, y generar recomendaciones priorizadas para el desarrollo de nuevos mecanismos detectivos de seguridad.

## 2. Arquitectura - Patrón MCP (Model-Controller-Plane)

La solución implementa una arquitectura MCP (Model Context Protocol) de **3 agentes secuenciales**, orquestados por CrewAI. Cada agente toma el output del anterior y lo enriquece, siguiendo un flujo lineal, robusto y auditable:

1. **ThreatAnalyzerAgent (Agente Analizador):**
    - Recibe el input del usuario (descripción de la aplicación).
    - Analiza debilidades y utiliza la herramienta RAG (DBIRRAGTool) para identificar hasta 5 amenazas relevantes del informe DBIR.
    - Output: Lista estructurada de hallazgos iniciales.
2. **RiskClassifierAgent (Agente Clasificador):**
    - Toma los hallazgos del analizador.
    - Usa la herramienta MitreAttackTool para mapear cada riesgo a TTPs (MITRE ATT&CK) y enriquecer la información.
    - Output: Hallazgos enriquecidos con mapeo MITRE.
3. **ReportingAgent (Agente de Reporte):**
    - Recibe los datos enriquecidos del clasificador.
    - Genera el reporte final en Markdown, priorizando detectores y pasos accionables claros para equipos de seguridad.

Todo el flujo está validado con modelos Pydantic y cuenta con logging exhaustivo para trazabilidad. La solución es 100% containerizada y soporta tanto LLM cloud (OpenAI) como local (Ollama).

## 🚀 Configuración y Ejecución

Este proyecto utiliza Poetry para la gestión de dependencias y Poe the Poet para la ejecución de tareas.

### Prerrequisitos

*   Instalar Python 3.11 o superior.
*   Instalar Poetry: Sigue las [instrucciones oficiales de instalación](https://python-poetry.org/docs/#installation).
*   **Clave de API de OpenAI:** Necesitarás una clave de API válida para OpenAI.

### Instalación del Proyecto (Desarrollo Local)

1.  **Clona el repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd meli-datasec-challenge
    ```

2.  **Crea tu archivo de entorno:**
    Copia el archivo de ejemplo y rellena tu clave de API de OpenAI.
    ```bash
    cp .env.example .env
    ```

3.  **Configura tu clave de OpenAI:**
    Edita el archivo `.env` y añade tu clave de API de OpenAI:
    ```
    OPENAI_API_KEY="tu_clave_de_api_de_openai_aqui"
    # Opcional: Puedes especificar un modelo diferente si lo deseas
    # OPENAI_MODEL_NAME="gpt-4-turbo"
    ```

4.  **Instala las dependencias y crea la base de datos RAG:**
    Este comando único instalará todo lo necesario y ejecutará el script de ingesta del DBIR.
    ```bash
    poetry install
    poetry run poe ingest
    ```
    *Nota: La primera vez, la ingesta puede tardar varios minutos.*

### Comandos Principales con Poe the Poet (Desarrollo Local)

Una vez instalado, puedes usar los siguientes comandos desde la raíz del proyecto:

*   **Iniciar la API (modo desarrollo):**
    ```bash
    poetry run poe api
    ```
    La API estará disponible en `http://localhost:8000`.

*   **Ejecutar la suite de tests:**
    ```bash
    poetry run poe test
    ```

*   **Ejecutar tests con reporte de cobertura:**
    ```bash
    poetry run poe test-cov
    ```

*   **Formatear el código (con Black):**
    ```bash
    poetry run poe format
    ```

## 🐳 Ejecución con Docker (Recomendado para Producción/Despliegue)

La aplicación está completamente containerizada para facilitar su despliegue.

1.  **Crea tu archivo de entorno:**
    Asegúrate de tener un archivo `.env` configurado con tu `OPENAI_API_KEY` como se describe en la sección de instalación.

2.  **Construye y levanta los contenedores:**
    ```bash
    docker-compose up --build
    ```
    Esto construirá la imagen de Docker (incluyendo la ingesta del DBIR) y levantará el servicio de la API. La API estará disponible en `http://localhost:8000`.

3.  **Acceder a la API:**
    Puedes interactuar con la API a través de `http://localhost:8000/docs` para ver la documentación de Swagger UI.

4.  **Detener los contenedores:**
    ```bash
    docker-compose down
    ```

## 3. Configuración del Proyecto

La configuración se gestiona a través de variables de entorno y el archivo `.env`. Consulta `src/config.py` para ver todas las variables disponibles y sus valores por defecto.

## 4. Estructura de Archivos Clave

*   `src/mcp_crews.py`: Orquestación MCP y definición de la Crew de 3 agentes.
*   `src/agents.py`: Define los 3 agentes MCP (Analizador, Clasificador, Reporte).
*   `src/llm_provider.py`: Selección y configuración de LLM (OpenAI/Ollama).
*   `src/config.py`: Configuración de la aplicación usando Pydantic Settings.
*   `api/`: Implementación de la API FastAPI.
*   `data/input/`: Informe DBIR (PDF).
*   `data/output/`: Reportes generados.
*   `vector_db/`: Base de datos vectorial para el RAG.
*   `tests/`: Tests unitarios y de integración.
*   `evaluation/validate_rag.py`: Script de evaluación de calidad RAG con RAGAs.

## 5. Evaluación de Calidad RAG (RAGAs)

Puedes evaluar la calidad del sistema RAG ejecutando el script `evaluation/validate_rag.py`, que utiliza el framework [RAGAs](https://github.com/explodinggradients/ragas) para calcular métricas como `context_precision` y `faithfulness` sobre un dataset de preguntas del DBIR.

### Ejecutar la evaluación RAG

1. Instala las dependencias de desarrollo (incluye ragas):
    ```bash
    poetry install --with dev
    ```
2. Ejecuta el script de evaluación:
    ```bash
    poetry run python evaluation/validate_rag.py
    ```
3. Se imprimirá un reporte con las métricas principales.

Puedes modificar el dataset de preguntas en el propio script para adaptarlo a tus necesidades.