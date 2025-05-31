# Use official Node.js LTS image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json ./

# Install dependencies
RUN npm install --production

# Copy the rest of the application code
COPY . .

# Expose the app port
EXPOSE 5000

# Set environment variables (can be overridden at runtime)
ENV NODE_ENV=production

# Start the server
CMD ["npm", "start"] 