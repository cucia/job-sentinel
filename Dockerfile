FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir --default-timeout=120 --retries=5 pyyaml flask playwright==1.57.0 docker
RUN chmod +x /app/scripts/start-xvfb.sh
ENV PYTHONPATH=/app
CMD ["python", "-m", "core.controller"]
