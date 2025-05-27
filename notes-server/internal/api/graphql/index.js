const { GraphQLSchema, GraphQLObjectType } = require('graphql');
const notePageQueries = require('./resolvers/noteQueries');
const notePageMutations = require('./resolvers/noteMutations');

const schema = new GraphQLSchema({
  query: new GraphQLObjectType({
    name: 'RootQueryType',
    fields: {
      ...notePageQueries
    }
  }),
  mutation: new GraphQLObjectType({
    name: 'Mutation',
    fields: {
      ...notePageMutations
    }
  })
});

module.exports = schema; 