const mongoose = require('mongoose');
const { DatabaseError } = require('../../../../pkg/utils/errorHandler');

const connectDB = async () => {
  try {
    await mongoose.connect(process.env.MONGODB_URI, {
      maxPoolSize: 10,
      minPoolSize: 2,
      maxIdleTimeMS: 30000,
      connectTimeoutMS: 10000,
      socketTimeoutMS: 45000,
      family: 4,
      retryWrites: true,
      w: 'majority',
      readPreference: 'secondaryPreferred',
      serverSelectionTimeoutMS: 5000,
      heartbeatFrequencyMS: 10000
    });

    
    mongoose.connection.on('connected', () => {
      console.log('Connected to MongoDB');
    });

    mongoose.connection.on('error', (err) => {
      console.error('MongoDB connection error:', err);
      throw new DatabaseError(`MongoDB connection error: ${err.message}`);
    });

    mongoose.connection.on('disconnected', () => {
      console.log('MongoDB disconnected');
    });

    // Handle process termination
    process.on('SIGINT', cleanup);
    process.on('SIGTERM', cleanup);

    return mongoose.connection;
  } catch (err) {
    console.error('MongoDB initial connection error:', err);
    throw new DatabaseError(`Failed to connect to MongoDB: ${err.message}`);
  }
};

const cleanup = async () => {
  try {
    await mongoose.connection.close();
    console.log('MongoDB connection closed through app termination');
    process.exit(0);
  } catch (err) {
    console.error('Error during MongoDB cleanup:', err);
    process.exit(1);
  }
};

// Helper function to check connection status
const isConnected = () => {
  return mongoose.connection.readyState === 1;
};

// Helper function to get connection stats
const getConnectionStats = () => {
  return {
    readyState: mongoose.connection.readyState,
    host: mongoose.connection.host,
    port: mongoose.connection.port,
    name: mongoose.connection.name,
    models: Object.keys(mongoose.connection.models)
  };
};

module.exports = { 
  connectDB, 
  cleanup,
  isConnected,
  getConnectionStats
}; 