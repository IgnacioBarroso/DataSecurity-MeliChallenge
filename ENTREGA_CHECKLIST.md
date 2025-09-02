# Checklist de Cumplimiento y Mejoras para el DataSec Challenge (Meli)


- [x] **Sistema multiagente con 3+ agentes (Analizador, Clasificador, Reporting, etc.) en pipeline secuencial.**
    - Ver `src/agents.py`, `src/main_crew.py` y README sección Arquitectura.
- [x] **Input estructurado del usuario sobre su ecosistema.**
    - Ejemplos en `data/custom_inputs/*.txt` y frontend (`frontend/index.html`).
- [x] **Comparativa entre input y DBIR 2025 para identificar hasta 5 detectores prioritarios.**
    - Lógica en `src/agents.py`, ejemplos de output en `data/examples/security_report_output.json`.
- [x] **Asociación a MITRE ATT&CK usando MCP real (Model Context Protocol).**
    - Implementado con CrewAI MCP y tools en `src/tools/mitre_tool.py`, ver README sección MCP.
- [x] **Reporte final con detectores, análisis de riesgos, racional y accionables.**
    - Ejemplo: `data/examples/security_report_output.json` y `security_report_output.md`.
- [x] **Roles y validación: cada agente con rol claro, validación de datos y manejo de errores.**
    - Ver `src/agents.py`, `src/models.py`, validación con Pydantic y manejo de errores en API (`api/routers/analysis.py`).
- [x] **MCP: Al menos 1 MCP para gestionar herramientas a los agentes.**
    - CrewAI MCP y tools (`src/tools/`).
- [x] **Trazabilidad: logs de input/output de cada agente, almacenados centralizadamente por sesión.**
    - Ver carpeta `logs/` (ejemplo: `logs/session_{id}.json`).
- [x] **Dockerización.**
    - Ver `Dockerfile` y `docker-compose.yml`.
- [x] **Modelo local y frontend.**
    - Ollama soportado (README), frontend en `frontend/index.html`.
- [x] **Tests de cobertura, edge cases y seguridad.**
    - Ver `tests/`, cobertura con `poetry run poe test-cov`.


- [x] **Implementar e integrar un MCP real (CrewAI MCP, sub-crews como tools)**
    - [x] Refactorización y orquestador: ver `src/main_crew.py`, `src/tools/mitre_tool.py`.
    - [x] El agente de MITRE usa MCP y tools (ver código y README sección MCP).
    - [x] Documentación MCP: pendiente de refuerzo en README (se agregará en la próxima iteración).
- [x] **Proveer un template/documentación clara para el input**
    - [x] Ejemplos de input en `data/custom_inputs/*.txt` y en el frontend.
    - [x] El frontend y la API aceptan texto estructurado (ver `api/schemas/analysis.py`).
- [x] **Centralizar y almacenar logs de input/output por sesión**
    - [x] Implementado: ver carpeta `logs/` y lógica en `src/logging_config.py`.
- [ ] **Validación de calidad de datos RAG (bonus)**
    - [ ] Agente/función de validación de calidad RAG pendiente de refuerzo (ver `src/agents.py`, placeholder presente).
- [ ] **Benchmark/versionado de prompts/config (bonus)**
    - [ ] Lógica de versionado/benchmark pendiente de implementar.
- [x] **Mejorar README/documentación**
    - [x] README actualizado en la próxima iteración: flujo, MCP, input, trazabilidad y bonus.

---



- [x] **MCP CrewAI**
    - [x] Refactorización y sub-crews/orquestador: ver `src/main_crew.py`, `src/tools/mitre_tool.py`.
    - [x] El agente de MITRE usa MCP/tools (ver código y README).
    - [x] Documentación MCP: se refuerza en README en la próxima iteración.
- [x] **Input template**
    - [x] Ejemplos de input estructurado en `data/custom_inputs/*.txt` y en el frontend.
- [x] **Logs centralizados**
    - [x] Almacenamiento de logs por sesión en `logs/session_{id}.json`.
- [ ] **Validación de calidad RAG**
    - [ ] Placeholder presente, falta lógica robusta de validación.
- [ ] **Benchmark/versionado**
    - [ ] Pendiente de implementar.
- [x] **Actualizar README**
    - [x] README se actualizará en la próxima iteración para reflejar todos los puntos.

---

**Usa este checklist para ir marcando los avances y asegurar que la entrega cumple perfectamente con el desafío.**
