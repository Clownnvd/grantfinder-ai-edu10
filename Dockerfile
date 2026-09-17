FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runtime

ENV PATH=/home/app/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app
WORKDIR /app

RUN useradd --create-home --uid 10001 app
COPY --from=builder /root/.local /home/app/.local
COPY --chown=app:app bff bff
COPY --chown=app:app grantfinder grantfinder
COPY --chown=app:app data data
COPY --chown=app:app artifacts artifacts
COPY --chown=app:app db db
COPY --chown=app:app scripts scripts

USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "bff.grant_main:app", "--host", "0.0.0.0", "--port", "8000"]
