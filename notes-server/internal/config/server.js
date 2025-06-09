const express = require('express');
const cors = require('cors');
const { logger, requestLogger } = require('../../pkg/utils/logger');
require('dotenv').config();

const config = {
  port: process.env.PORT || 5000,
  nodeEnv: process.env.NODE_ENV || 'development',
  mongodb: {
    uri: process.env.MONGODB_URI || 'mongodb+srv://ahmedelhadi1777:fb5OpNipjvS65euk@cluster0.ojy4aft.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0',
    options: {
      maxPoolSize: parseInt(process.env.MONGODB_MAX_POOL_SIZE) || 50,
      minPoolSize: parseInt(process.env.MONGODB_MIN_POOL_SIZE) || 10,
      maxIdleTimeMS: parseInt(process.env.MONGODB_MAX_IDLE_TIME_MS) || 30000,
      connectTimeoutMS: parseInt(process.env.MONGODB_CONNECT_TIMEOUT_MS) || 5000,
      serverSelectionTimeoutMS: parseInt(process.env.MONGODB_SERVER_SELECTION_TIMEOUT_MS) || 5000,
    }
  },
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT) || 6380,
    password: process.env.REDIS_PASSWORD || '',
    db: parseInt(process.env.REDIS_DB) || 2,
  },
  jwt: {
    secret: process.env.JWT_SECRET || 'a82552a2c8133eddce94cc781f716cdcb911d065528783a8a75256aff6731886',
    algorithm: process.env.JWT_ALGORITHM || 'HS256',
    expiryHours: parseInt(process.env.JWT_EXPIRY_HOURS) || 24,
  },
  cors: {
    origin: process.env.CORS_ORIGINS ? process.env.CORS_ORIGINS.split(',') : ['http://localhost:3000', 'http://localhost:8080'],
    credentials: true
  },
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: process.env.LOG_FORMAT || 'combined'
  }
};

const configureServer = (app) => {
  app.use(cors(config.cors));
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

module.exports = { configureServer, config }; 