# Stage 1: Build Frontend
FROM node:18-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Server
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and dataset
COPY backend/ ./backend/
COPY dataset/ ./dataset/
COPY .env .

# Copy built frontend from Stage 1 to backend/static
COPY --from=frontend-build /app/frontend/dist ./backend/static

# Ensure the static directory exists and contains index.html
RUN ls -la ./backend/static

# Expose port
EXPOSE 8000

# Set Python path and run server
ENV PYTHONPATH=.
CMD ["python", "backend/run_server.py"]
