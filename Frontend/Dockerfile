# syntax=docker/dockerfile:1
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps
COPY . .
RUN npm run build

# This stage only builds the frontend assets.
# The static files will be served by the main NGINX gateway container.

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /etc/nginx/certs

EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"] 