FROM python:3.12-alpine

RUN apk add --no-cache iproute2 coreutils procps

COPY app.py /app.py

CMD ["python", "/app.py"]
