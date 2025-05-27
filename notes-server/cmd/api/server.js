require('dotenv').config();

const express = require('express');
const cors = require('cors');
const { graphqlHTTP } = require('express-graphql');
const mongoose = require('mongoose');
const { connectDB } = require('../../internal/infrastructure/persistence/mongodb/connection');
const schema = require('../../internal/api/graphql');
const { formatGraphQLError } = require('../../pkg/utils/errorHandler');
const { limiter } = require('../../internal/api/middleware/rateLimiter');
const RedisClient = require('../../internal/infrastructure/cache/redis');
const redisConfig = require('../../internal/infrastructure/cache/config');

const app = express();
let server;
let redisClient;

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  const dbStatus = mongoose.connection.readyState === 1 ? 'connected' : 'disconnected';
  const redisStatus = redisClient?.isHealthy() ? 'connected' : 'disconnected';
  
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    database: dbStatus,
    redis: redisStatus
  });
});

// Connect to MongoDB and initialize rate limiter
const initializeServer = async () => {
  try {
    // Connect to MongoDB
    await connectDB();
    
    // Initialize Redis
    redisClient = new RedisClient(redisConfig);
    
    // Make Redis client available globally
    global.redisClient = redisClient;
    
    // GraphQL endpoint with rate limiting
    app.use('/graphql', limiter, graphqlHTTP({
      schema,
      graphiql: true,
      customFormatErrorFn: formatGraphQLError
    }));

    // Error handling middleware for non-GraphQL errors
    app.use((err, req, res, next) => {
      console.error(err.stack);
      
      const status = err.status || 500;
      const errorResponse = {
        success: false,
        message: err.message || 'Internal Server Error',
        errors: [{
          message: err.message || 'Internal Server Error',
          code: err.code || 'INTERNAL_ERROR'
        }]
      };
      
      res.status(status).json(errorResponse);
    });

    const PORT = process.env.PORT || 5000;

    // Start server
    server = app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });

    // Handle server-specific shutdown
    const gracefulShutdown = async () => {
      console.log('Starting graceful shutdown...');
      
      // Close Redis connection
      if (redisClient) {
        await redisClient.close();
        console.log('Redis connection closed');
      }
      
      // Close server
      if (server) {
        server.close(() => {
          console.log('Express server closed');
        });
      }
    };

    // Handle various shutdown signals
    process.on('SIGTERM', gracefulShutdown);
    process.on('SIGINT', gracefulShutdown);
    
    // Handle uncaught errors
    process.on('uncaughtException', (error) => {
      console.error('Uncaught Exception:', error);
      gracefulShutdown();
    });
    
    process.on('unhandledRejection', (error) => {
      console.error('Unhandled Rejection:', error);
      gracefulShutdown();
    });
  } catch (error) {
    console.error('Failed to initialize server:', error);
    process.exit(1);
  }
};

initializeServer();
