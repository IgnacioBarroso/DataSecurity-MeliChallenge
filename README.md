# Sistema Multiagente Autónomo para la Detección de Amenazas

Proyecto para el “DataSec Challenge” de Mercado Libre. Implementa un sistema multiagente con RAG (DBIR 2025), mapeo a MITRE ATT&CK (MCP externo), generación de reportes priorizados y trazabilidad completa por sesión.

## Arquitectura General

- 3 agentes secuenciales (CrewAI): Analizador → Clasificador → Reporte.
- RAG sobre DBIR (PDF) con Chroma DB (REST) y docstore persistente (Redis) usando ParentDocumentRetriever.
- MCP externo de MITRE ATT&CK en contenedor dedicado (clona el repo oficial y expone herramientas MCP por HTTP).
- API FastAPI con endpoints de análisis y RAG; UI estática servida por la API; healthchecks de servicios.
- Trazas por sesión en JSON para auditar inputs/outputs de tareas y herramientas.

## Requisitos

- Python 3.11+
- Docker + Docker Compose
- Clave de API de OpenAI (`OPENAI_API_KEY`)

## Configuración Rápida (Docker)

1) Copia y edita entorno
- `cp .env.example .env`
- Define al menos `OPENAI_API_KEY`. Recomendado: `OPENAI_MODEL_NAME=gpt-4.1-mini` para mejor calidad en reportes largos.

2) Construye imágenes
- `docker-compose build`

3) Ingesta del DBIR (una vez o cuando cambie el PDF)
- `docker-compose run --rm dbir-ingest`

4) Levanta servicios (un único stack)
- `docker-compose up -d mitre-mcp chromadb redis datasec-agent`
- Accesos:
  - API: `http://localhost:8000` (docs `/docs`, UI `/ui`, health `/health`)
  - MCP MITRE: `http://localhost:8080`
  - ChromaDB REST: `http://localhost:8001`

5) Detener servicios
- `docker-compose down`

## Configuración (.env)

- `OPENAI_API_KEY`: requerido (embeddings y LLM)
- `OPENAI_MODEL_NAME`: por defecto `gpt-4.1-nano`
- `COHERE_API_KEY`: opcional (re-ranking Cohere). Si falta, se aplica MMR local (semántico)
- `CHROMA_DB_HOST`/`CHROMA_DB_PORT`: por defecto `chromadb:8000` (servicio REST de compose)
- `REDIS_HOST`/`REDIS_PORT`/`REDIS_DB`: por defecto `redis:6379` (habilita docstore persistente)
- `LLM_PROVIDER`: `openai` (por defecto) o `ollama` (local)
  - Para Ollama: `OLLAMA_BASE_URL` y `OLLAMA_MODEL` (p.ej., `llama3`). Servicio opcional en compose.
- `ANALYZER_MODE`: `heavy` (por defecto) o `turbo`. Es el modo por defecto del backend si no se especifica `mode` en la request.
  - `heavy` (calidad completa):
    - Arquitectura de 3 agentes (CrewAI) con MultiQueryRetriever y Cohere Rerank (si `COHERE_API_KEY`), MMR si no hay Cohere.
    - MCP externo como preferido; fallback explícito a herramientas locales (`attackcti`) si MCP no está disponible.
    - Logging detallado y trazas activas (verbose True).
    - Estructura de reporte idéntica a `turbo`; `timing_ms` dentro del JSON del reporte y en la respuesta de la API.
  - `turbo` (máxima velocidad, misma estructura de salida):
    - Pipeline single‑pass sin CrewAI; sin MultiQuery ni Cohere; reuso y cache global de RAG/LLM.
    - MCP externo únicamente (sin fallback local) para minimizar overhead.
    - k reducido, `max_tokens` acotado y logs en WARNING.
    - Estructura de reporte idéntica a `heavy`; `timing_ms` dentro del JSON del reporte y en la respuesta de la API.

### Cambio de modo en tiempo real (sin reiniciar)
- UI: en `/ui` hay un switch “Modo: Turbo/Heavy” que invoca el backend con `?mode=` por-request.
- API: también se puede cambiar por-request usando `?mode=heavy|turbo` en:
  - `POST /api/analyze?mode=turbo`
  - `POST /api/analyze-upload?mode=heavy`
- Nota: el modo TURBO se puede forzar por-request aunque `ANALYZER_MODE` global sea `heavy`. El backend respeta `?mode=turbo` sin reinicios ni cambios de entorno.

## API Endpoints

- `GET /`: estado básico de la API
- `GET /health`: healthcheck enriquecido
  - Campos: `api`, `redis`, `vector_db`, `mcp`, `mcp_dns`, `chroma`, `chroma_collection`, `chroma_count`
- `POST /api/analyze`: ejecuta pipeline multiagente (3 agentes)
  - Request: `{ "user_input": "texto..." }`
  - Response: `{ "report_json": "{...}", "session_id": "..." }`
- `POST /api/rag/ask`: pregunta directa al RAG
  - Request: `{ "question": "..." }`
  - Response: `{ "answer": "...", "context_preview": "..." }`
- `POST /api/rag/debug`: auditoría del RAG (documentos, similitudes, selección MMR)
  - Request: `{ "question": "..." }`
  - Response: `{ "question": "...", "docs": [{"score": float, "selected": bool, "text_preview": str}, ...] }`
- UI estática: `GET /ui`

## Modos de Ejecución: Heavy vs Turbo

- Propósito: ambos producen el mismo formato FinalReport (JSON), difieren en arquitectura y performance.
- Heavy:
  - 3 agentes CrewAI (Analizador → Clasificador → Reporte) con trazabilidad detallada.
  - Recuperación avanzada (MultiQueryRetriever); opcional CohereRerank si `COHERE_API_KEY` está presente.
  - Fallback local a MITRE (attackcti) si el MCP externo no está disponible.
  - Mayor costo/latencia, máxima calidad y explicabilidad.
- Turbo:
  - Pipeline single‑pass (sin CrewAI) con recuperación directa y generación del reporte final.
  - Sin CohereRerank; menor k y `max_tokens` amplios para completar 5 detectores.
  - Usa el MCP externo; sin fallback local para minimizar overhead.
  - Mucho más rápido, mismo esquema de salida (FinalReport) validado.

Selección de modo:
- Por defecto, `ANALYZER_MODE` en `.env` (heavy o turbo).
- Por request: `?mode=heavy|turbo` en los endpoints de análisis.

## CLI

- Analizar archivo (respeta `ANALYZER_MODE`):
  - `python main.py analyze path/al/archivo.txt --output salida.json`
- Pregunta directa al RAG:
  - `python main.py rag "¿Cuál es el vector de ataque más común?"`

Benchmark modos (opcional):
- `poetry run python evaluation/benchmark_modes.py` (compara tiempos entre `heavy` y `turbo` en CLI RAG)

## RAG: Ingesta y Recuperación

- Ingesta (`docker-compose run --rm dbir-ingest`):
  - Procesa `data/input/2025-dbir-data-breach-investigations-report.pdf` con Unstructured
  - Divide jerárquicamente (padre 2000c, hijo 400c)
  - Indexa en Chroma (colección `dbir_2025`) y guarda docstore en Redis si está configurado
- Recuperación (consultas):
  - ParentDocumentRetriever con Redis Docstore (si activo) o retriever vectorial simple
  - Re-ranking: CohereRerank si `COHERE_API_KEY` está definido (se usa directamente como compresor en `ContextualCompressionRetriever`); de lo contrario, MMR semántico local sobre hasta 20 documentos (con embeddings OpenAI)
  - Contexto sintetizado y limitado para el prompt del LLM

## MCP MITRE ATT&CK

- Servicio `mitre-mcp` clona `https://github.com/stoyky/mitre-attack-mcp` y expone `:8080` (interno y host) para el servidor FastMCP (HTTP SSE).
- Carga de herramientas (por modo):
  - `turbo`: usa únicamente herramientas del MCP externo (no hay fallback, para minimizar overhead).
  - `heavy`: prioriza herramientas del MCP externo; si MCP no está disponible, hace fallback explícito a herramientas locales basadas en `attackcti`.

## Trazabilidad y Logs

- Por cada ejecución se genera un `session_id` y se registran:
  - `logs/session_<id>.log`: logs generales
  - `logs/session_<id>_trace.json`: trazas estructuradas de tareas y herramientas (input/output/errors)

## Evaluación de Calidad (RAGAs)

- Script: `evaluation/validate_rag.py`
  - Usa el pipeline real (`ask_rag`) para obtener `answers` y `retrieved_contexts`
  - Calcula métricas `context_precision` y `faithfulness`
- Ejecutar:
  - `poetry install --with dev`
  - `poetry run python evaluation/validate_rag.py`

## Desarrollo Local (Poetry)

- Instalar dependencias: `poetry install`
- Ingesta local (fuera de Docker): `poetry run poe ingest` (requiere `.env` coherente)
- API (dev): `poetry run poe api`
- Tests: `poetry run poe test` (E2E desactivado por defecto; exporta `RUN_E2E=1` para habilitar)
- Formato: `poetry run poe format`

## Estructura de Carpetas (Clave)

- `src/mcp_crews.py`: orquestación de agentes y trazas por tarea
- `src/agents.py`: definición de los 3 agentes
- `src/tools/`: herramientas (DBIR RAG, MITRE, cliente MCP externo)
- `src/rag_system/`: ingesta y retriever avanzado (ParentDocumentRetriever + Redis Docstore)
- `src/config.py`: configuración (Pydantic Settings)
- `src/trace.py`: control del trace logger global
- `api/`: FastAPI (routers, servicios, app)
- `data/input/`: PDF del DBIR
- `frontend/`: UI estática servida por la API en `/ui`
- `docker-compose.yml`, `docker/`: contenedores (MCP, app), servicios (Chroma, Redis, Ollama opcional)

## Consejos y Solución de Problemas

- Ingesta no ejecuta en build: usa `docker-compose run --rm dbir-ingest`
- Health `/health` ahora intenta obtener la colección y el conteo de documentos:
  - Si usas el servicio `chromadb` de compose, tras `docker-compose run --rm dbir-ingest` deberías ver `"chroma": "ok"`, `"chroma_collection": "present"` y `"chroma_count": <n>`.
  - El healthcheck usa primero el SDK de Chroma vía REST; si no puede, intenta REST puro como fallback.
- Sin Cohere: el reranking MMR está activo y ofrece buena precisión sin costo adicional
- MCP offline: el sistema continúa con `attackcti` local; para habilitar MCP levanta `mitre-mcp`
- Ollama: opcional; si no usas LLM local, omite el servicio

## Cumplimiento del Challenge

- 3 agentes con roles claros y validación Pydantic
- DBIR 2025 como base (RAG jerárquico, Chroma + Redis docstore)
- Mapeo MITRE ATT&CK con MCP externo y fallback local
- Reporte final JSON priorizado y accionable
- Trazabilidad completa por agente/herramienta
- Dockerización profesional y reproducible (servicios separados, healthchecks, volúmenes persistentes)
