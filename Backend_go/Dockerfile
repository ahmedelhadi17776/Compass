# Build stage
FROM golang:1.24-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git

# Copy go mod and sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy the source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -o main ./cmd/api

# Final stage
FROM alpine:latest

# Add non root user
RUN adduser -D -g '' appuser

WORKDIR /app

# Copy the binary and config from builder
COPY --from=builder /app/main .
COPY --from=builder /app/pkg/config/config.docker.yaml ./pkg/config/config.yaml
COPY --from=builder /app/migrations ./migrations

# Create necessary directories and set permissions
RUN mkdir -p /app/pkg/config && \
    chown -R appuser:appuser /app

# Set environment variables
ENV SERVER_PORT=8000 \
    SERVER_MODE=development \
    REDIS_HOST=redis \
    REDIS_PORT=6379 \
    REDIS_PASSWORD="" \
    REDIS_DB=0 \
    JWT_ISSUER=compass-api \
    JWT_EXPIRY_HOURS=24 \
    LOG_LEVEL=info \
    LOG_FORMAT=json

# Switch to non root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/api/health || exit 1

# Run the binary
CMD ["./main"] 