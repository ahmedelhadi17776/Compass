const rateLimit = require('express-rate-limit');
const MongoStore = require('rate-limit-mongo');
const mongoose = require('mongoose');
const { DatabaseError } = require('../../../pkg/utils/errorHandler');

if (!process.env.MONGODB_URI) {
  throw new Error('MONGODB_URI environment variable is required for rate limiting');
}

// Rate limiting configuration
const limiter = rateLimit({
  store: new MongoStore({
    uri: process.env.MONGODB_URI,
    collectionName: 'rate-limits',
    expireTimeMs: 15 * 60 * 1000, // 15 minutes
    mongoOptions: {
      useExistingConnection: mongoose,
      retryWrites: true
    },
    errorHandler: (err) => {
      console.error('Rate limit store error:', err);
      throw new DatabaseError(`Rate limit store error: ${err.message}`);
    }
  }),
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
  message: {
    success: false,
    message: 'Too many requests, please try again later.',
    errors: [{
      message: 'Rate limit exceeded',
      code: 'RATE_LIMIT_EXCEEDED',
      retryAfter: 15 * 60 
    }]
  },
  skip: (req) => {
    return req.path === '/health' || req.method === 'OPTIONS';
  },
  keyGenerator: (req) => {
    // Use IP and user ID if available for better rate limiting
    return req.user ? `${req.ip}-${req.user.id}` : req.ip;
  },
  handler: (req, res) => {
    res.status(429).json({
      success: false,
      message: 'Too many requests, please try again later.',
      errors: [{
        message: 'Rate limit exceeded',
        code: 'RATE_LIMIT_EXCEEDED',
        retryAfter: 15 * 60
      }]
    });
  }
});

// Helper function to get rate limit info
const getRateLimitInfo = (req) => {
  const store = limiter.store;
  return {
    windowMs: limiter.windowMs,
    max: limiter.max,
    current: store.getKey ? store.getKey(req) : null
  };
};

module.exports = { limiter, getRateLimitInfo };