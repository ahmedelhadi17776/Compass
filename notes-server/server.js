const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const { graphqlHTTP } = require('express-graphql');
const { connectDB } = require('./config/db.config');
const schema = require('./graphql/schema');
const { formatGraphQLError } = require('./utils/errorHandler');

dotenv.config();

const app = express();
let server;

// Middleware
app.use(cors());
app.use(express.json());

// Connect to MongoDB and initialize rate limiter
const initializeServer = async () => {
  await connectDB();
  
  // Import rate limiter after DB connection is established
  const limiter = require('./config/ratelimiter');
  
  // GraphQL endpoint with rate limiting
  app.use('/graphql', limiter, graphqlHTTP({
    schema,
    graphiql: true,
    customFormatErrorFn: formatGraphQLError
  }));

  // Error handling middleware for non-GraphQL errors
  app.use((err, req, res, next) => {
    console.error(err.stack);
    
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

  const PORT = process.env.PORT || 5000;

  // Start server
  server = app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });

  // Handle server-specific shutdown
  const gracefulShutdown = async () => {
    console.log('Starting graceful shutdown...');
    
    // Close server first
    if (server) {
      server.close(() => {
        console.log('Express server closed');
      });
    }
  };

  // Handle various shutdown signals
  process.on('SIGTERM', gracefulShutdown);
  process.on('SIGINT', gracefulShutdown);
  
  // Handle uncaught errors
  process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
    gracefulShutdown();
  });
  
  process.on('unhandledRejection', (error) => {
    console.error('Unhandled Rejection:', error);
    gracefulShutdown();
  });
};

initializeServer().catch(err => {
  console.error('Failed to initialize server:', err);
  process.exit(1);
});
