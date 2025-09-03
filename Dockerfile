
# Dockerfile

ARG DEBIAN_FRONTEND=noninteractive

# --- Etapa 1: Builder ---
FROM python:3.11-slim AS builder

# Dependencias del sistema necesarias para build/ingesta (lxml/unstructured)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -

# Crear venv dentro del proyecto para poder copiarlo
RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true

WORKDIR /app

# Copiar solo los archivos de dependencias para aprovechar cache
COPY pyproject.toml poetry.lock ./

# Instalar dependencias de producción
RUN poetry install --no-interaction --no-ansi --no-dev

# --- Etapa 2: Final ---
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependencias del sistema necesarias en runtime para PDF/Unstructured
RUN apt-get update \
    && apt-get install -y --no-install-recommends poppler-utils libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar entorno virtual desde builder y usarlo
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto de la API
EXPOSE 8000

# Añadir usuario no-root
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Comando para iniciar el servidor de la API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
