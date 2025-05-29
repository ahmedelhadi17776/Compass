function generateEntityKey(keyPrefix, entityType, entityId, action = '') {
  return `${keyPrefix}${entityType}:${entityId}${action ? ':' + action : ''}`;
}

function generateListKey(userId, entityType, params = {}) {
  const paramString = Object.entries(params).sort().map(([k, v]) => `${k}:${JSON.stringify(v)}`).join('|');
  return `user:${userId}:${entityType}:${paramString}`;
}

function generateTagSetKey(keyPrefix, tag) {
  return `${keyPrefix}tag:${tag}`;
}

module.exports = {
  generateEntityKey,
  generateListKey,
  generateTagSetKey
}; 