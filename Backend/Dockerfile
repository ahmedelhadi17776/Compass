# 1. Builder stage
FROM python:3.11.9-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies and then clean up apt cache to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Set up a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .

# Upgrade pip and install wheel to ensure we use pre-compiled binaries
RUN pip install --upgrade pip wheel

# Install PyTorch first from the official CPU-only wheel index.
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the requirements.
RUN pip install --no-cache-dir -r requirements.txt

# 2. Production stage
FROM python:3.11.9-slim-bookworm AS production

# Apply security updates from the base image and install curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl && apt-get upgrade -y --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a non-root user and set ownership before copying files
RUN addgroup --system app && adduser --system --group app && \
    mkdir -p /app/writable/logs /app/writable/cache /app/cache && \
    chown -R app:app /app/writable /app/cache

# Switch to non-root user
USER app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code with correct ownership
COPY --chown=app:app . .

# Make virtual environment available
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"] 