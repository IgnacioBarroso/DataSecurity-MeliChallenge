# Sistema Multiagente Autónomo para la Detección de Amenazas

## 1. Descripción General del Proyecto

Este proyecto es una implementación del "DataSec Challenge" de Mercado Libre. El objetivo es desarrollar un sistema multiagente autónomo que utiliza IA para analizar inteligencia de amenazas (basada en el Verizon DBIR 2025) en el contexto de una aplicación interna específica, y generar recomendaciones priorizadas para el desarrollo de nuevos mecanismos detectivos de seguridad.

## 2. Arquitectura - Patrón MCP (Model-Controller-Plane)

La solución se basa en una arquitectura de agentes secuenciales orquestada por el framework CrewAI, siguiendo el patrón **Model-Controller-Plane (MCP)**. En este patrón, el output de una sub-crew se convierte en el input de la siguiente, creando un flujo de trabajo lineal y controlado.

El sistema consta de las siguientes sub-crews, cada una con agentes especializados:

*   **Input Parsing Crew:** Estructura el input del usuario en un `EcosystemContext`.
*   **Threat Intelligence Crew:** Identifica amenazas usando el informe DBIR vía RAG y las valida.
*   **MITRE Classification Crew:** Mapea amenazas a MITRE ATT&CK y asigna riesgos.
*   **Reporting Crew:** Genera el informe final con recomendaciones accionables.

El sistema está diseñado para ser robusto, con validación de datos entre agentes mediante Pydantic y un logging exhaustivo por sesión para garantizar la trazabilidad. Toda la solución está containerizada con Docker para facilitar su ejecución.

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

*   `src/mcp_crews.py`: Contiene la implementación de la orquestación MCP y las definiciones de las sub-crews.
*   `src/agents.py`: Define los agentes individuales utilizados en las crews.
*   `src/llm_provider.py`: Gestiona la inicialización del LLM (actualmente OpenAI).
*   `src/config.py`: Configuración de la aplicación usando Pydantic Settings.
*   `api/`: Contiene la implementación de la API FastAPI.
*   `data/input/`: Ubicación del informe DBIR (PDF).
*   `data/output/`: Donde se guardan los reportes generados.
*   `vector_db/`: Base de datos vectorial para el RAG.
*   `tests/`: Tests unitarios y de integración.