FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Kolkata

WORKDIR /app
COPY . /app
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get update \
    && apt-get install -y tzdata xvfb fluxbox x11vnc novnc websockify \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir --default-timeout=120 --retries=5 pyyaml flask playwright==1.57.0 docker
RUN chmod +x /app/scripts/start-xvfb.sh /app/scripts/start-dashboard-gui.sh
ENV PYTHONPATH=/app
CMD ["python", "-m", "src.core.controller"]
