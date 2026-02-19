FROM python:3.11-slim

ARG POETRY_VERSION=1.5.1
ENV POETRY_VERSION=${POETRY_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Leverage layer caching by copying dependency metadata first
COPY pyproject.toml poetry.lock* /app/

RUN pip install --upgrade pip \
    && pip install "poetry==${POETRY_VERSION}" \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi --no-dev

# Copy application source after dependencies to keep rebuilds fast
COPY . /app

# Create a non-root user and give ownership of the app directory
RUN useradd --create-home app \
    && chown -R app:app /app

USER app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
