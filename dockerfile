FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "app.py"]
