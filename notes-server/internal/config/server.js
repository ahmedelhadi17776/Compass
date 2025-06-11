const express = require('express');
const cors = require('cors');
const { logger } = require('../../pkg/utils/logger');
const { requestLogger } = require('../api/middleware');

const configureServer = (app) => {
  app.use(cors());
  app.use(express.json());
  app.use(requestLogger);

  // Error handling middleware
  app.use((err, req, res, next) => {
    logger.error('Unhandled error', { 
      error: err.stack,
      path: req.path,
      method: req.method,
      ip: req.ip
    });
    
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

  return app;
};

module.exports = configureServer; 