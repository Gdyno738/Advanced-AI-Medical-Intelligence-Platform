# ---- Frontend Build Stage ----
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_BASE_URL=""
RUN npm run build

# ---- Backend & Unified App Stage ----
FROM python:3.12-slim

WORKDIR /app

# DevOps Memory Optimization: Pre-install CPU-only PyTorch to save ~2GB of RAM/Disk on free tiers
RUN pip install --no-cache-dir torch==2.13.0 torchvision==0.28.0 --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
# DevOps Fix: Libraries like grad-cam secretly install the GUI 'opencv-python'.
# We uninstall all cv2 packages and forcefully reinstall the headless version to avoid missing C-libraries.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y opencv-python opencv-python-headless && \
    pip install --no-cache-dir opencv-python-headless==5.0.0.93

# Copy application code
COPY app/ ./app/
COPY models/ ./models/

# Create necessary directories
RUN mkdir -p reports uploads app/db

# Copy built React frontend into the static directory
COPY --from=frontend-build /app/dist /app/static

# Expose port (default 7860 for HF Spaces, but PaaS can override)
ENV PORT=7860
EXPOSE ${PORT}

# Command to run FastAPI
CMD ["sh", "-c", "uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
