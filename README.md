Sistema Multiagente Autónomo para la Detección de Amenazas

1. Descripción General del Proyecto


Este proyecto es una implementación del "DataSec Challenge" de Mercado Libre. El objetivo es desarrollar un sistema multiagente autónomo que utiliza IA para analizar inteligencia de amenazas (basada en el Verizon DBIR 2025) en el contexto de una aplicación interna específica, y generar recomendaciones priorizadas para el desarrollo de nuevos mecanismos detectivos de seguridad.


2. Arquitectura

La solución se basa en una arquitectura de agentes secuenciales orquestada por el framework CrewAI, con un total de 5 agentes:
*   **Input Parsing Agent:** Estructura el input del usuario.
*   **RAG Threat Analyzer:** Identifica amenazas usando el informe DBIR vía RAG.
*   **RAG Quality Validator:** Valida la trazabilidad de los hallazgos del RAG.
*   **TTP Risk Classifier:** Mapea amenazas a MITRE ATT&CK y asigna riesgos.
*   **Actionable Reporting Specialist:** Genera el informe final con recomendaciones accionables.

El sistema está diseñado para ser robusto, con validación de datos entre agentes mediante Pydantic y un logging exhaustivo por sesión para garantizar la trazabilidad. Toda la solución está containerizada con Docker para facilitar su ejecución.

## 🚀 Configuración y Ejecución con Poetry

Este proyecto utiliza Poetry para la gestión de dependencias y Poe the Poet para la ejecución de tareas.

### Prerrequisitos

*   Instalar Python 3.11 o superior.
*   Instalar Poetry: Sigue las [instrucciones oficiales de instalación](https://python-poetry.org/docs/#installation).

### Instalación del Proyecto

1.  **Clona el repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd meli-datasec-challenge
    ```

2.  **Crea tu archivo de entorno:**
    Copia el archivo de ejemplo y rellena tus claves de API.
    ```bash
    cp .env.example .env
    ```

3.  **Instala las dependencias y crea la base de datos RAG:**
    Este comando único instalará todo lo necesario y ejecutará el script de ingesta del DBIR.
    ```bash
    poetry install
    poetry run poe ingest
    ```
    *Nota: La primera vez, la ingesta puede tardar varios minutos.*

### Comandos Principales con Poe the Poet

Una vez instalado, puedes usar los siguientes comandos desde la raíz del proyecto:

*   **Iniciar la API (modo desarrollo):**
    ```bash
    poetry run poe api
    ```
    La API estará disponible en `http://localhost:8000`.

*   **Ejecutar la herramienta CLI:**
    ```bash
    poetry run poe cli -- data/examples/input_example_1.txt
    ```

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





3. Configuración del Proyecto


   1. **Clonar el repositorio:**bash
git clone <URL_DEL_REPOSITORIO>
cd meli-datasec-challenge

   2. Crear el archivo de entorno:
Copie el archivo de ejemplo y complete las variables de entorno requeridas.
Bash
cp.env.example.env

Edite el archivo .env y añada su clave de API (por ejemplo, GOOGLE_API_KEY).
   3. Instalar dependencias (opcional, para desarrollo local):
Se recomienda ejecutar el proyecto a través de Docker. Sin embargo, si desea ejecutarlo localmente, instale las dependencias:
Bash
pip install -r requirements.txt

## Cómo Cambiar entre LLMs (Online vs. Local)

Este proyecto está diseñado para funcionar tanto con un modelo en la nube (Google Gemini) como con un modelo local a través de [Ollama](https://ollama.com/), para permitir el desarrollo sin conexión y proteger la privacidad de los datos.

### Prerrequisitos para el LLM Local

1.  **Instalar Ollama:** Sigue las instrucciones en su sitio web para instalar Ollama en tu sistema operativo.
2.  **Descargar un Modelo:** Ejecuta en tu terminal el comando para descargar el modelo que desees. Se recomienda `llama3` por su buen equilibrio entre rendimiento y tamaño.
    ```bash
    ollama pull llama3
    ```
3.  **Verificar que Ollama esté en ejecución:** Asegúrate de que la aplicación de Ollama esté corriendo en tu máquina.

### Configuración

El cambio entre modelos se gestiona a través de variables en el archivo `.env`:

1.  **Para usar Google Gemini (Online):**
    Asegúrate de que tu archivo `.env` se vea así:
    ```
    LLM_PROVIDER="google"
    GEMINI_API_KEY="tu_api_key_real_aqui"
    ```

2.  **Para usar Ollama (Local):**
    Modifica tu archivo `.env` para que apunte a tu instancia local:
    ```
    LLM_PROVIDER="local"
    OLLAMA_BASE_URL="http://host.docker.internal:11434"
    OLLAMA_MODEL="llama3" 
    ```
    *   **`OLLAMA_BASE_URL`**: `http://host.docker.internal:11434` es la dirección recomendada para que el contenedor Docker se comunique con Ollama en tu máquina.
    *   **`OLLAMA_MODEL`**: Debe coincidir con el nombre del modelo que descargaste.

Una vez que hayas guardado los cambios en el archivo `.env`, simplemente reconstruye y reinicia tu contenedor con `docker-compose up --build` para que los cambios surtan efecto.
