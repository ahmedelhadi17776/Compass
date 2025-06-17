# Stage 1: Build the frontend assets
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY Frontend/package*.json ./
RUN npm ci --legacy-peer-deps
COPY Frontend/ ./
RUN npm run build

# Stage 2: Set up the Nginx server
FROM nginx:alpine
# Copy the built frontend assets from the builder stage
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy the Nginx configuration
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copy SSL certificates
COPY certs /etc/nginx/certs

# Ensure non-root user can write logs
RUN chown -R nginx:nginx /var/cache/nginx /var/log/nginx /etc/nginx/certs && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Switch to non-root user for security
USER nginx

EXPOSE 80
EXPOSE 443

CMD ["nginx", "-g", "daemon off;"] 