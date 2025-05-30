FROM pytorch/pytorch:2.1.0-cpu-py310

WORKDIR /app
COPY app.py .

# Install required Python packages
RUN pip install --no-cache-dir \
    flask \
    transformers \
    python-dateutil

ENV FAIL_AFTER=30

CMD ["python", "app.py"]
