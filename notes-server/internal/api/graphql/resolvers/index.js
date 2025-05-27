const noteQueries = require('./noteQueries');
const noteMutations = require('./noteMutations');

module.exports = {
  Query: {
    ...noteQueries
  },
  Mutation: {
    ...noteMutations
  }
}; 