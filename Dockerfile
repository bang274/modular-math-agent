# HuggingFace Spaces Dockerfile
# Runs both backend (FastAPI) and frontend (built static files) in one container.

FROM python:3.11-slim AS backend-deps
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# Install Redis
RUN apt-get update && apt-get install -y --no-install-recommends redis-server nginx && \
    rm -rf /var/lib/apt/lists/*

# Copy Python deps
COPY --from=backend-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-deps /usr/local/bin /usr/local/bin

# Copy backend
COPY backend/ /app/backend/
COPY .env.example /app/backend/.env

# Copy frontend build
COPY --from=frontend-build /app/dist /app/frontend-dist

# Nginx config for serving frontend + proxying API
RUN echo 'server { \
    listen 7860; \
    root /app/frontend-dist; \
    index index.html; \
    location / { try_files $uri $uri/ /index.html; } \
    location /api/ { proxy_pass http://127.0.0.1:8000; proxy_set_header Host $host; } \
    location /ws/ { proxy_pass http://127.0.0.1:8000; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; } \
    location /docs { proxy_pass http://127.0.0.1:8000; } \
    location /redoc { proxy_pass http://127.0.0.1:8000; } \
}' > /etc/nginx/conf.d/default.conf

# Create data directory inside backend/ where app expects it
RUN mkdir -p /app/backend/data && chmod 777 /app/backend/data

# Start script
RUN echo '#!/bin/bash\n\
redis-server --daemonize yes\n\
cd /app/backend && uvicorn app.main:app --host 127.0.0.1 --port 8000 &\n\
nginx -g "daemon off;"' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 7860

CMD ["/app/start.sh"]
