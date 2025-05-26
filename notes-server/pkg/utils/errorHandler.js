const { z } = require('zod');

class NotFoundError extends Error {
  constructor(resource) {
    super(`${resource} not found`);
    this.resource = resource;
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

  if (originalError instanceof NotFoundError) {
    return {
      message: originalError.message,
      code: 'NOT_FOUND',
      status: 404
    };
  }

  // Handle other types of errors
  return {
    message: error.message || 'Internal Server Error',
    code: 'INTERNAL_ERROR',
    status: 500,
    locations: error.locations,
    path: error.path
  };
};

module.exports = {
  NotFoundError,
  handleZodError,
  formatGraphQLError
}; 