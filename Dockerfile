# ---- Frontend Build Stage ----
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_BASE_URL=""
RUN npm run build

# ---- Backend & Unified App Stage ----
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY models/ ./models/

# Create necessary directories
RUN mkdir -p reports uploads app/db

# Copy built React frontend into the static directory
COPY --from=frontend-build /app/dist /app/static

# Expose port 7860 (Hugging Face Default)
EXPOSE 7860

# Command to run FastAPI
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
