const { GraphQLSchema, GraphQLObjectType } = require('graphql');
const notePageQueries = require('./resolvers/noteQueries');
const notePageMutations = require('./resolvers/noteMutations');
const journalQueries = require('./resolvers/journalQueries');
const journalMutations = require('./resolvers/journalMutations');

const schema = new GraphQLSchema({
  query: new GraphQLObjectType({
    name: 'RootQueryType',
    fields: {
      ...notePageQueries,
      ...journalQueries
    }
  }),
  mutation: new GraphQLObjectType({
    name: 'Mutation',
    fields: {
      ...notePageMutations,
      ...journalMutations
    }
  })
});

module.exports = schema;