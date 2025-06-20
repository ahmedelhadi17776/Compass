# Stage 1: Build the frontend assets
FROM node:19.0.1-alpine AS frontend-builder
WORKDIR /app

# First, copy the .dockerignore file and then the package files
COPY Frontend/.dockerignore ./.dockerignore
COPY Frontend/package*.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy the rest of the frontend source code
COPY Frontend/ ./

# Build the frontend
RUN npm run build

# Stage 2: Set up the Nginx server
FROM nginx:1.25-alpine

# Copy the Nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy the built frontend assets from the builder stage
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy SSL certificates
COPY certs /etc/nginx/certs

# Create a directory for Nginx to store its PID file and ensure it's owned by the nginx user.
# Nginx automatically handles log file permissions when run as a non-root user.
RUN mkdir -p /var/run/nginx && \
    chown -R nginx:nginx /var/run/nginx && \
    chown -R nginx:nginx /var/cache/nginx

# Switch to the non-root user for security
USER nginx

EXPOSE 80
EXPOSE 443

CMD ["nginx", "-g", "daemon off;"] 