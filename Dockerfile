FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache \
    iproute2 \
    coreutils \
    procps \
    wget \
    gcc \
    musl-dev \
    linux-headers

WORKDIR /app

COPY app.py .
COPY templates ./templates
COPY static ./static

RUN pip install --no-cache-dir flask psutil

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ || exit 1

CMD ["python", "app.py"]
