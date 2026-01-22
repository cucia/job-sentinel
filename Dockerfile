FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir pyyaml playwright
RUN python -m playwright install --with-deps chromium
ENV PYTHONPATH=/app
CMD ["python", "-m", "core.controller"]
