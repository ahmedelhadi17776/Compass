const rateLimit = require('express-rate-limit');
const MongoStore = require('rate-limit-mongo');
const mongoose = require('mongoose');

// Rate limiting configuration
const limiter = rateLimit({
    store: new MongoStore({
      uri: process.env.MONGODB_URI,
      collectionName: 'rate-limits',
      expireTimeMs: 15 * 60 * 1000, // 15 minutes
      mongoOptions: {
        useExistingConnection: mongoose // Use existing mongoose connection
      }
    }),
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests per windowMs
    message: {
      success: false,
      message: 'Too many requests, please try again later.',
      errors: [{
        message: 'Rate limit exceeded',
        code: 'RATE_LIMIT_EXCEEDED'
      }]
    }
  });

module.exports = limiter;