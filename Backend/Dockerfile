# 1. Builder stage
FROM python:3.11-slim-bullseye AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y build-essential

# Set up a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Production stage
FROM python:3.11-slim-bullseye AS production

WORKDIR /app

# Create a non-root user
RUN addgroup --system app && adduser --system --group app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Set ownership and permissions
RUN chown -R app:app /app
USER app

# Make virtual environment available
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"] 