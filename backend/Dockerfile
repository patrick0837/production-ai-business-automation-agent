FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir -r /app/backend/requirements.txt

RUN addgroup --system app && adduser --system --ingroup app app

COPY --chown=app:app backend /app/backend
COPY --chown=app:app alembic.ini /app/alembic.ini
COPY --chown=app:app alembic /app/alembic

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

USER app

CMD ["celery", "-A", "backend.app.worker.celery_app:celery_app", "worker", "--loglevel=INFO"]