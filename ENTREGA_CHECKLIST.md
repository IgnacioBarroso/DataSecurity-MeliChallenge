# Checklist de Cumplimiento y Mejoras para el DataSec Challenge (Meli)

## 1. Revisión exhaustiva del desafío y requerimientos
- [x] Sistema multiagente con 3 agentes (Analizador, Clasificador, Reporting) en pipeline secuencial.
- [x] Input estructurado del usuario sobre su ecosistema (template específico).
- [x] Comparativa entre input y DBIR 2025 para identificar hasta 5 detectores prioritarios (Alto/Medio/Bajo riesgo).
- [x] Asociación a MITRE ATT&CK usando un MCP existente (Model Context Protocol) para mapear detectores a técnicas y clasificar riesgos.
- [x] Reporte final con detectores, análisis de riesgos, racional y accionables.
- [x] Roles y validación: cada agente con rol claro, validación de datos y manejo de errores.
- [ ] MCP: Al menos 1 MCP (puede ser de la comunidad) para gestionar/otorgar herramientas a los agentes.
- [x] Trazabilidad: logs de input/output de cada agente, almacenados centralizadamente por sesión.
- [x] Dockerización.
- [x] Modelo local y frontend.
- [x] Tests de cobertura, edge cases y seguridad.

## 2. Lo que falta o debe mejorarse según el challenge
- [ ] **Implementar e integrar un MCP real**
    - [ ] Investigar e integrar un MCP existente (por ejemplo, para MITRE ATT&CK) o crear uno propio simple.
    - [ ] Hacer que al menos un agente (idealmente el clasificador de MITRE) use el MCP para acceder a herramientas o datos.
    - [ ] Documentar en el README cómo se usa el MCP y su propósito.
- [ ] **Proveer un template/documentación clara para el input**
    - [ ] Añadir un ejemplo de input estructurado en el README y/o en un archivo aparte.
    - [ ] Asegurarse de que el frontend y la API acepten y validen este formato.
- [ ] **Centralizar y almacenar logs de input/output por sesión**
    - [ ] Implementar un sistema de logging centralizado (por ejemplo, un archivo JSON por sesión o una base de datos simple).
    - [ ] Cada ejecución debe guardar los input/output de cada agente con un identificador de sesión.
- [ ] **Validación de calidad de datos RAG (bonus)**
    - [ ] Añadir un agente o función que valide la calidad de los fragmentos recuperados por RAG (por ejemplo, checking de relevancia, longitud, etc.).
- [ ] **Benchmark/versionado de prompts/config (bonus)**
    - [ ] Implementar lógica para versionar prompts/config y/o comparar resultados entre modelos/configuraciones.
- [ ] **Mejorar README/documentación**
    - [ ] Explicar claramente el flujo, el uso de MCP, el formato de input, y cómo se almacena la trazabilidad.

---

## 3. Resumen de acciones concretas a realizar

- [ ] **MCP**
    - [ ] Buscar/integrar un MCP de la comunidad (ejemplo: mitre-attack-mcp) o crear uno propio simple.
    - [ ] Hacer que el agente de MITRE lo use para mapear amenazas a técnicas.
    - [ ] Documentar el uso y propósito del MCP.
- [ ] **Input template**
    - [ ] Añadir un ejemplo de input estructurado en el README y/o en un archivo `input_template.json`.
- [ ] **Logs centralizados**
    - [ ] Implementar almacenamiento de logs de input/output por sesión (por ejemplo, en `logs/session_{id}.json`).
- [ ] **Validación de calidad RAG**
    - [ ] Añadir un validador de calidad de fragmentos RAG (puede ser un agente o función).
- [ ] **Benchmark/versionado**
    - [ ] Añadir lógica para versionar prompts/config y/o comparar resultados.
- [ ] **Actualizar README**
    - [ ] Explicar el flujo, el MCP, el input, la trazabilidad y los bonus implementados.

---

**Usa este checklist para ir marcando los avances y asegurar que la entrega cumple perfectamente con el desafío.**
