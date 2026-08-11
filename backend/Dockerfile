FROM python:3.10-slim

WORKDIR /app

# System dependencies for OpenCV and MediaPipe
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/
COPY ai_engine/requirements.txt /app/ai_engine/

RUN pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r ai_engine/requirements.txt

COPY . /app

EXPOSE 8000

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
