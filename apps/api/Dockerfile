ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN addgroup --system app && adduser --system --ingroup app app

COPY apps/api/requirements.txt /tmp/requirements.txt
# RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN pip install --upgrade pip -i https://mirrors.cloud.tencent.com/pypi/simple/ --trusted-host mirrors.cloud.tencent.com \
    && pip install --no-cache-dir --default-timeout=120 --retries 10 -i https://mirrors.cloud.tencent.com/pypi/simple/ --trusted-host mirrors.cloud.tencent.com -r /tmp/requirements.txt

COPY apps/api /app
COPY apps/api/start.sh /start.sh
RUN chown -R app:app /app && chmod +x /start.sh

USER app

EXPOSE 8000

CMD ["/start.sh"]
