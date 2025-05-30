FROM python:3.10-slim

WORKDIR /app
COPY fail_app.py .

# Install required Python packages
RUN pip install flask transformers python-dateutil

ENV FAIL_AFTER=30

CMD ["python", "app.py"]
