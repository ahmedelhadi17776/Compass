const jwt = require('jsonwebtoken');

function extractUserIdFromToken(authorization) {
  if (!authorization || !authorization.startsWith('Bearer ')) {
    throw new Error('Invalid or missing token');
  }
  const token = authorization.split(' ')[1];
  try {
    const claims = jwt.verify(token, process.env.JWT_SECRET, {
      algorithms: [process.env.JWT_ALGORITHM || 'HS256']
    });
    if (!claims.user_id && !claims.userId) {
      throw new Error('user_id not found in token');
    }
    return claims.user_id || claims.userId;
  } catch (e) {
    throw new Error(`Token decode error: ${e.message}`);
  }
}

module.exports = { extractUserIdFromToken }; 