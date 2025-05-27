const { z } = require('zod');
const { logger } = require('./logger');

class BaseError extends Error {
  constructor(message, code = 'INTERNAL_ERROR') {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.timestamp = new Date().toISOString();
    
    // Log the error
    logger.error(message, {
      error: {
        name: this.name,
        code: this.code,
        stack: this.stack
      }
    });
  }
}

class ValidationError extends BaseError {
  constructor(message, field = null) {
    super(message, 'VALIDATION_ERROR');
    this.field = field;
  }
}

class NotFoundError extends BaseError {
  constructor(entity) {
    super(`${entity} not found`, 'NOT_FOUND');
    this.entity = entity;
  }
}

class DatabaseError extends BaseError {
  constructor(message) {
    super(message, 'DATABASE_ERROR');
  }
}

class AuthenticationError extends BaseError {
  constructor(message) {
    super(message, 'AUTHENTICATION_ERROR');
  }
}

class AuthorizationError extends BaseError {
  constructor(message) {
    super(message, 'AUTHORIZATION_ERROR');
  }
}

const handleZodError = (error) => {
  if (!(error instanceof z.ZodError)) {
    throw error;
  }

  logger.warn('Zod Validation Error', { errors: error.errors });
  return error.errors.map(err => ({
    message: err.message,
    field: err.path.join('.'),
    code: 'VALIDATION_ERROR'
  }));
};

const formatGraphQLError = (error) => {
  const originalError = error.originalError;
  
  if (originalError instanceof BaseError) {
    return {
      message: originalError.message,
      code: originalError.code,
      field: originalError.field,
      timestamp: originalError.timestamp
    };
  }

  // Log unexpected errors
  logger.error('Unexpected GraphQL error', {
    error: {
      message: error.message,
      stack: error.stack,
      originalError: originalError?.message
    }
  });

  return {
    message: 'An unexpected error occurred',
    code: 'INTERNAL_ERROR',
    timestamp: new Date().toISOString()
  };
};

module.exports = {
  BaseError,
  ValidationError,
  NotFoundError,
  DatabaseError,
  AuthenticationError,
  AuthorizationError,
  handleZodError,
  formatGraphQLError
}; 