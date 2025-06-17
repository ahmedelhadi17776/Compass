# 1. Build stage
FROM node:20-alpine AS builder
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy the rest of the application source code
COPY . .

# (Optional) Add a build step when set it
# RUN npm run build

# 2. Production stage
FROM node:20-alpine
WORKDIR /app

# Create a non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy dependencies from the builder stage
COPY --from=builder /app/node_modules ./node_modules
# Copy application code
COPY . .

# Set correct permissions
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

EXPOSE 5000

# Start the server
CMD ["node", "cmd/api/server.js"] 