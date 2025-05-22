# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

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
    pip install --no-cache-dir --retries 10 --timeout 300 torch==2.7.0 && \
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

# Install the package in development mode
RUN pip install -e .

# Copy .env file
COPY .env .env

# Expose the FastAPI port
EXPOSE 8001

RUN mkdir -p /app/certs

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"] 