FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache \
    iproute2 \
    gcc \
    musl-dev \
    linux-headers

WORKDIR /app

COPY app.py .
COPY templates ./templates
COPY static ./static

RUN pip install --no-cache-dir flask psutil \
 && apk del gcc musl-dev linux-headers

EXPOSE 80

CMD ["python", "app.py"]
