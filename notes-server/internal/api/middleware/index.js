const { requestLogger } = require('../../../pkg/utils/logger');
const createRateLimiter = require('./rateLimiter');

function userContextMiddleware(req, res, next) {
  const userId = req.header('X-User-Id');
  if (userId) {
    req.user = { id: userId };
  }
  next();
}

module.exports = {
  requestLogger,
  createRateLimiter,
  userContextMiddleware
}; 