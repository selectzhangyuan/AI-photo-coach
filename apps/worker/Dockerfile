ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN addgroup --system app && adduser --system --ingroup app app

COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY apps/api /app
RUN chown -R app:app /app

USER app

CMD ["celery", "-A", "app.core.celery_app.celery_app", "worker", "--loglevel=info", "-Q", "analysis"]
