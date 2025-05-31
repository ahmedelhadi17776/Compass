const noteQueries = require('./noteQueries');
const noteMutations = require('./noteMutations');
const journalQueries = require('./journalQueries');
const journalMutations = require('./journalMutations');

module.exports = {
  Query: {
    ...noteQueries,
    ...journalQueries
  },
  Mutation: {
    ...noteMutations,
    ...journalMutations
  }
};