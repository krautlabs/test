# --- First stage: tester ---
FROM python:3.13-slim AS tester

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir hatch pytest

COPY . .

RUN hatch build \
 && pip install --no-cache-dir dist/*.whl \
 && rm -rf src

RUN pytest


# --- Second stage: final image ---
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir hatch

COPY . .

RUN hatch build \
 && pip install --no-cache-dir dist/*.whl

WORKDIR /data

ENTRYPOINT ["pycheese"]
