const { logger } = require('../../pkg/utils/logger');

const setupShutdownHandlers = (server, redisClient) => {
  const gracefulShutdown = async () => {
    logger.info('Starting graceful shutdown...');
    
    // Close Redis connection
    if (redisClient) {
      await redisClient.close();
      logger.info('Redis connection closed');
    }
    
    // Close server
    if (server) {
      server.close(() => {
        logger.info('Express server closed');
      });
    }
  };

  // Handle various shutdown signals
  process.on('SIGTERM', gracefulShutdown);
  process.on('SIGINT', gracefulShutdown);
  
  // Handle uncaught errors
  process.on('uncaughtException', (error) => {
    logger.error('Uncaught Exception', { 
      error: error.stack,
      message: error.message
    });
    gracefulShutdown();
  });
  
  process.on('unhandledRejection', (error) => {
    logger.error('Unhandled Rejection', { 
      error: error.stack,
      message: error.message
    });
    gracefulShutdown();
  });
};

module.exports = setupShutdownHandlers; 