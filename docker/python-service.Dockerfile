# syntax=docker/dockerfile:1.6
ARG PYTHON_VERSION=3.11-slim
FROM python:${PYTHON_VERSION} AS runtime

ARG SERVICE_PATH

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/service/src

WORKDIR /service

RUN apt-get update \
     && apt-get install -y --no-install-recommends \
         build-essential \
         libpq-dev \
         curl \
    && rm -rf /var/lib/apt/lists/*

COPY ${SERVICE_PATH}/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ${SERVICE_PATH}/ /service/

EXPOSE 5000

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000", "--no-reload"]
