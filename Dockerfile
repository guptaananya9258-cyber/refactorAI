### Build frontend
FROM node:18 AS builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./frontend/
COPY frontend/ ./frontend/
WORKDIR /app/frontend
RUN npm ci --silent || npm install
RUN npm run build

### Build backend image
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend build
COPY backend/ ./backend/
COPY --from=builder /app/frontend/dist ./frontend/dist

ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "1"]
FROM python:3.11-slim
WORKDIR /app
COPY . /app

# Install system deps for building and runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

# Use gunicorn for production
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "4"]
