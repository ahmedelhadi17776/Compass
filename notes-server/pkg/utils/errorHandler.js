const { z } = require('zod');

class BaseError extends Error {
  constructor(message, code, status) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.status = status;
    Error.captureStackTrace(this, this.constructor);
  }
}

class ValidationError extends BaseError {
  constructor(message, field) {
    super(message, 'VALIDATION_ERROR', 400);
    this.field = field;
  }
}

class NotFoundError extends BaseError {
  constructor(resource) {
    super(`${resource} not found`, 'NOT_FOUND', 404);
    this.resource = resource;
  }
}

class DatabaseError extends BaseError {
  constructor(message) {
    super(message, 'DATABASE_ERROR', 500);
  }
}

const handleZodError = (error) => {
  if (!(error instanceof z.ZodError)) {
    throw error;
  }

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
      status: originalError.status,
      field: originalError.field,
      resource: originalError.resource
    };
  }

  return {
    message: error.message || 'Internal Server Error',
    code: 'INTERNAL_ERROR',
    status: 500,
    locations: error.locations,
    path: error.path
  };
};

module.exports = {
  BaseError,
  ValidationError,
  NotFoundError,
  DatabaseError,
  handleZodError,
  formatGraphQLError
}; 