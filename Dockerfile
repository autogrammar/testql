FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY testql/ ./testql/

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app

ENTRYPOINT ["testql"]
CMD ["--help"]
