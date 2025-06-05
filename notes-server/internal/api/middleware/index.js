const { requestLogger } = require('../../../pkg/utils/logger');
const createRateLimiter = require('./rateLimiter');
const { extractUserIdFromToken } = require('../../../pkg/utils/jwt');

function userContextMiddleware(req, res, next) {
  let userId = null;
  if (req.headers.authorization) {
    try {
      userId = extractUserIdFromToken(req.headers.authorization);
    } catch (e) {
      return res.status(401).json({ success: false, message: e.message });
    }
  }
  if (!userId) {
    return res.status(401).json({ success: false, message: 'Authorization token required' });
  }
  req.user = { id: userId };
  next();
}

module.exports = {
  requestLogger,
  createRateLimiter,
  userContextMiddleware
}; 