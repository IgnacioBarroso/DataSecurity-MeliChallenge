
#######################################################################
# Dockerfile multi-stage para la app DataSec (API + RAG + agentes)
#
# - Stage builder: instala dependencias con Poetry en un venv in-project
# - Stage final: imagen ligera con runtime + venv copiado
# - Se evita compilar en la imagen final; se usan solo binarios del venv
# - Poppler/libmagic se incluyen para Unstructured y manejo de PDFs
#######################################################################

ARG DEBIAN_FRONTEND=noninteractive

# ---------- Stage 1: Builder ----------
FROM python:3.11-slim AS builder

# Dependencias para compilar wheels/lxml y descargar Poetry
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry en /opt/poetry y agregar al PATH
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -

# Configurar virtualenv dentro del proyecto (para copiarlo luego)
RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true

WORKDIR /app

# Copiar únicamente archivos de dependencias para aprovechar la cache de capas
COPY pyproject.toml poetry.lock ./

# Instalar dependencias de producción (sin dev) sin instalar el paquete raíz
RUN poetry install --no-interaction --no-ansi --without dev --no-root

# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

# Ajustes de Python: no pyc, salida no bufferizada
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependencias del sistema necesarias en tiempo de ejecución
# - poppler-utils: para parseo de PDF con unstructured
# - libmagic1: detección de tipos de archivo
RUN apt-get update \
    && apt-get install -y --no-install-recommends poppler-utils libmagic1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar el entorno virtual desde el builder y usarlo por defecto
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto de la API FastAPI
EXPOSE 8000

# Ejecutar como usuario no root por seguridad
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Comando de entrada: ejecuta la API Uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
