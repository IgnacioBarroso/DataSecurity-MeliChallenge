
# Dockerfile

# --- Etapa 1: Builder ---
# Esta etapa instala todas las dependencias, incluyendo las de desarrollo.
FROM python:3.11-slim AS builder

# Instalar Poetry
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -

# Configurar Poetry para no crear entornos virtuales dentro del proyecto
RUN poetry config virtualenvs.create false

WORKDIR /app

# Copiar solo los archivos de dependencias para aprovechar el cache de Docker
COPY pyproject.toml poetry.lock ./ 

# Instalar dependencias de producción
# --no-dev asegura que los paquetes de testing no se incluyan en la capa final
RUN poetry install --no-interaction --no-ansi --no-dev

# --- Etapa 2: Final ---
# Esta etapa crea la imagen final, que es mucho más ligera.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Copiar el entorno virtual con las dependencias desde la etapa 'builder'
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copiar todo el código de la aplicación
COPY . .

# Ejecutar la ingesta de datos durante el build para que la base de datos esté lista
# Nota: Esto asume que el PDF está en el contexto de build.
RUN python -m src.rag_system.ingest

# Exponer el puerto de la API
EXPOSE 8000

# Añadir usuario no-root
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Comando para iniciar el servidor de la API
USER appuser

# Comando para iniciar el servidor de la API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
