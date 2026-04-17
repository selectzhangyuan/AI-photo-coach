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

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
