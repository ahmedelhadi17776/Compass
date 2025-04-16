# Build stage
FROM golang:1.24-alpine AS builder

WORKDIR /app

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

WORKDIR /app

# Copy the binary and config from builder
COPY --from=builder /app/main .
COPY --from=builder /app/pkg/config/config.yaml ./pkg/config/

# Create necessary directories
RUN mkdir -p /app/pkg/config

# Set environment variables
ENV DB_HOST=postgres \
    DB_PORT=5432 \
    DB_USER=ahmed \
    DB_PASSWORD=0502747598 \
    DB_NAME=compass \
    DB_SSLMODE=disable \
    SERVER_PORT=8000 \
    SERVER_MODE=development

# Expose port
EXPOSE 8000

# Run the binary
CMD ["./main"] 