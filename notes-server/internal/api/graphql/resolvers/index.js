const noteQueries = require('./noteQueries');
const noteMutations = require('./noteMutations');
const journalQueries = require('./journalQueries');
const journalMutations = require('./journalMutations');
const { withFilter } = require('graphql-subscriptions');
const { pubsub } = require('../../../infrastructure/cache/pubsub');

module.exports = {
  Query: {
    ...noteQueries,
    ...journalQueries
  },
  Mutation: {
    ...noteMutations,
    ...journalMutations
  },
  Subscription: {
    notePageCreated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator('NOTE_PAGE_CREATED'),
        (payload, variables, context) => {
          return payload.notePageCreated.data.userId === variables.userId;
        }
      )
    },
    notePageUpdated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator('NOTE_PAGE_UPDATED'),
        (payload, variables, context) => {
          return payload.notePageUpdated.data.userId === variables.userId;
        }
      )
    },
    notePageDeleted: {
      subscribe: withFilter(
        () => pubsub.asyncIterator('NOTE_PAGE_DELETED'),
        (payload, variables, context) => {
          return payload.notePageDeleted.data.userId === variables.userId;
        }
      )
    },
    journalCreated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator('JOURNAL_CREATED'),
        (payload, variables, context) => {
          return payload.journalCreated.data.userId === variables.userId;
        }
      )
    },
    journalUpdated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator('JOURNAL_UPDATED'),
        (payload, variables, context) => {
          return payload.journalUpdated.data.userId === variables.userId;
        }
      )
    },
    journalDeleted: {
      subscribe: withFilter(
        () => pubsub.asyncIterator('JOURNAL_DELETED'),
        (payload, variables, context) => {
          return payload.journalDeleted.data.userId === variables.userId;
        }
      )
    }
  }
};