require('dotenv').config();

const express = require('express');
const { logger } = require('../../pkg/utils/logger');
const { createRateLimiter } = require('../../internal/api/middleware');
const healthRoutes = require('../../internal/api/routes/health');
const graphqlRoutes = require('../../internal/api/routes/graphql');
const configureServer = require('../../internal/config/server');
const setupShutdownHandlers = require('../../internal/config/shutdown');
const initializeDatabases = require('../../internal/config/database');

const app = express();
let server;
let redisClient;

// Configure server middleware and error handling
configureServer(app);

// Initialize server
const initializeServer = async () => {
  try {
    logger.info('Initializing server...');
    
    // Initialize databases
    redisClient = await initializeDatabases();
    
    // Initialize rate limiter with Redis client
    const { limiter, rateLimitHeaders, getRateLimitInfo } = createRateLimiter(redisClient);
    logger.info('Rate limiter initialized');
    
    // Apply rate limiting middleware globally
    app.use(limiter);
    app.use(rateLimitHeaders);

    // Routes
    app.use('/health', healthRoutes);
    app.use('/graphql', graphqlRoutes);

    // Add rate limit info endpoint
    app.get('/rate-limit-info', async (req, res) => {
      try {
        const info = await getRateLimitInfo(req);
        logger.debug('Rate limit info requested', { info });
        res.json(info);
      } catch (error) {
        logger.error('Error getting rate limit info', { error: error.message });
        res.status(500).json({
          success: false,
          message: 'Error getting rate limit info',
          error: error.message
        });
      }
    });

    const PORT = process.env.PORT || 5000;

    // Start server
    server = app.listen(PORT, () => {
      logger.info(`Server running on port ${PORT}`);
    });

    // Setup shutdown handlers
    setupShutdownHandlers(server, redisClient);

  } catch (error) {
    logger.error('Failed to initialize server', { 
      error: error.stack,
      message: error.message
    });
    process.exit(1);
  }
};

initializeServer();
