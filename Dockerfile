# Stage 1: Build Frontend SPA
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Serve Backend & Static Frontend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend files
COPY backend/ ./backend/

# Copy built frontend dist from Stage 1 for single-link deploy
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist/

ENV PORT=8000
ENV PYTHONPATH=/app/backend

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
