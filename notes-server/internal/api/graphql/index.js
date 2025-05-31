const { GraphQLSchema, GraphQLObjectType } = require('graphql');
const notePageQueries = require('./resolvers/noteQueries');
const notePageMutations = require('./resolvers/noteMutations');
const journalQueries = require('./resolvers/journalQueries');
const journalMutations = require('./resolvers/journalMutations');
const { noteSubscriptionFields } = require('./schemas/noteTypes');
const { journalSubscriptionFields } = require('./schemas/journalTypes');

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
  }),
  subscription: new GraphQLObjectType({
    name: 'Subscription',
    fields: {
      ...noteSubscriptionFields,
      ...journalSubscriptionFields
    }
  })
});

// Attach subscription resolvers to schema fields
const subscriptionResolvers = require('./resolvers').Subscription;
const subscriptionType = schema.getSubscriptionType();
if (subscriptionType) {
  const fields = subscriptionType.getFields();
  for (const key of Object.keys(subscriptionResolvers)) {
    if (fields[key] && typeof subscriptionResolvers[key].subscribe === 'function') {
      fields[key].subscribe = subscriptionResolvers[key].subscribe;
    }
  }
}

module.exports = schema;