FROM python:3.10-slim

WORKDIR /app
COPY app.py .

# Install system dependencies for building PyTorch
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install required Python packages including PyTorch
RUN pip install --no-cache-dir \
    flask \
    transformers \
    torch \
    python-dateutil

ENV FAIL_AFTER=30

CMD ["python", "app.py"]
