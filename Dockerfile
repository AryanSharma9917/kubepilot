FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY agent ./agent
COPY rag ./rag
COPY services ./services
COPY docs ./docs

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "kubepilot_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
