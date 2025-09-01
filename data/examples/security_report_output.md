# Reporte de Seguridad: MeliInternal-FinanceDashboard

**ID del Reporte:** `a1b2c3d4-e5f6-7890-1234-567890abcdef`

## Resumen Ejecutivo

Este informe describe los 5 principales detectores de seguridad priorizados para desarrollar, basados en un análisis del contexto de la aplicación MeliInternal-FinanceDashboard frente a las amenazas destacadas en el Verizon DBIR 2025. El análisis se ha centrado en los riesgos más plausibles dada la naturaleza sensible de los datos financieros que maneja la aplicación.

---

## Detectores Priorizados

### 1. Monitoreo de Exfiltración de Datos Anómala vía API
*   **Nivel de Riesgo:** `Alto`
*   **Vector de Amenaza:** Abuso de privilegios por parte de usuarios internos.
*   **Técnicas MITRE ATT&CK:** `T1530` (Data from Cloud Storage Object), `T1048` (Exfiltration Over Alternative Protocol)

**Justificación:**
La aplicación maneja datos financieros altamente sensibles y tiene roles de usuario escalonados. Un atacante que comprometa una cuenta de 'Gerente' o 'Admin' podría exfiltrar datos críticos a través de la API. Esto se alinea con el patrón de 'Abuso de Privilegios' en el DBIR.

**Pasos Accionables:**
1.  Implementar un baseline del comportamiento normal de la API por rol de usuario (ej. volumen de datos, frecuencia de acceso, horarios).
2.  Crear una alerta en el SIEM que se dispare cuando un usuario exceda en 3 desviaciones estándar su comportamiento normal de descarga de datos.
3.  Registrar y auditar todas las consultas a endpoints de la API que devuelvan grandes volúmenes de datos.

### 2. Intentos de Fuerza Bruta en Endpoint de Autenticación
*   **Nivel de Riesgo:** `Alto`
*   **Vector de Amenaza:** Ataques a aplicaciones web para obtener credenciales.
*   **Técnicas MITRE ATT&CK:** `T1110` (Brute Force)

**Justificación:**
Dado que la aplicación protege datos financieros, el endpoint de autenticación es un objetivo principal. El DBIR 2025 sigue destacando los ataques de credenciales como un vector de acceso común.

**Pasos Accionables:**
1.  Implementar limitación de velocidad (rate limiting) en el endpoint de la API de inicio de sesión (ej. 5 intentos fallidos por minuto por IP).
2.  Desarrollar una regla de detección para alertar sobre múltiples intentos de inicio de sesión fallidos desde una única dirección IP en un corto período de tiempo.
3.  Asegurar que existan políticas de bloqueo de cuentas después de un número determinado de intentos fallidos.