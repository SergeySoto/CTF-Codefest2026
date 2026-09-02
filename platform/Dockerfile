FROM python:3.12-slim AS base

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV CTF_DB=/data/ctf.db PYTHONUNBUFFERED=1
EXPOSE 8000

# Etapa de desarrollo: el código llega por volumen, no se copia.
FROM base AS dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Etapa del evento: el código va dentro de la imagen.
FROM base AS prod
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
