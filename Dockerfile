FROM python:3.10-slim

WORKDIR /app
COPY fail_app.py .

RUN pip install flask

ENV FAIL_AFTER=30

CMD ["python", "fail_app.py"]
