# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TRANSFORMERS_CACHE=/app/cache/transformers \
    SENTENCE_TRANSFORMERS_HOME=/app/cache/sentence-transformers

# Set work directory
WORKDIR /app

# Create cache directories
RUN mkdir -p /app/cache/transformers \
    /app/cache/sentence-transformers \
    /app/ai_services/rag/chroma_store

# Install system dependencies
RUN apt-get update && \
    apt-get install -y build-essential gcc gnupg curl && \
    # Install MongoDB tools
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
    gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor && \
    echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | \
    tee /etc/apt/sources.list.d/mongodb-org-7.0.list && \
    apt-get update && \
    apt-get install -y mongodb-mongosh curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies with retry mechanism
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    # Install PyTorch 
    pip install --no-cache-dir --retries 10 --timeout 300 --resume-retries=5 torch==2.7.0 && \
    pip install --no-cache-dir --retries 10 --timeout 300 numpy && \
    pip install --no-cache-dir --retries 10 --timeout 300 scipy==1.11.4 && \
    # Install MongoDB dependencies first
    pip install --no-cache-dir pymongo==4.6.1 motor==3.3.2 && \
    # Install remaining requirements
    pip install --no-cache-dir --retries 10 --timeout 300 -r requirements.txt

# Copy project
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh


# Copy .env file
COPY .env .env

# Expose the FastAPI port
EXPOSE 8001

RUN mkdir -p /app/certs

# Healthcheck (optional, but recommended)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Use CMD to start your app (adjust as needed for your app)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"] 