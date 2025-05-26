const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const { graphqlHTTP } = require('express-graphql');
const connectDB = require('./config/db.config');
const schema = require('./graphql/schema');

dotenv.config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Connect to MongoDB
connectDB();

// GraphQL endpoint
app.use('/graphql', graphqlHTTP({
  schema,
  graphiql: true // Enable GraphiQL interface for testing in development
}));

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ message: 'Something went wrong!' });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
