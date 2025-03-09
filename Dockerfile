FROM python:3.13-slim

WORKDIR /app
COPY disk_bloater.py /app/
RUN chmod +x /app/disk_bloater.py

ENTRYPOINT ["python", "-u", "/app/disk_bloater.py"]