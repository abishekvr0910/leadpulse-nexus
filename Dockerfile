FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system leadpulse \
    && adduser --system --ingroup leadpulse leadpulse

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=leadpulse:leadpulse . .

USER leadpulse
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
