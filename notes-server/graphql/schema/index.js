const { GraphQLSchema, GraphQLObjectType } = require('graphql');
const notePageQueries = require('./Repository/notePage.query');
const notePageMutations = require('./handlers/notePage.mutation');

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