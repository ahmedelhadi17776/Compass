const { ApolloClient, InMemoryCache, split, HttpLink } = require('@apollo/client/core');
const { GraphQLWsLink } = require('@apollo/client/link/subscriptions');
const { createClient } = require('graphql-ws');
const { getMainDefinition } = require('@apollo/client/utilities');
const WebSocket = require('ws');
const fetch = require('cross-fetch');
const gql = require('graphql-tag');

// Set your test userId here or use process.env.TEST_USER_ID
const userId = process.env.TEST_USER_ID || '11e41910-a77c-4818-b073-28019b0fbc92';

const wsLink = new GraphQLWsLink(createClient({
  url: 'ws://localhost:5000/notes/graphql',
  webSocketImpl: WebSocket,
  connectionParams: {
    'X-User-Id': userId
  }
}));

const httpLink = new HttpLink({
  uri: 'http://localhost:5000/notes/graphql',
  fetch,
  headers: {
    'X-User-Id': userId
  }
});

const link = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink
);

const client = new ApolloClient({
  link,
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: { fetchPolicy: 'no-cache' },
    query: { fetchPolicy: 'no-cache' },
    mutate: { fetchPolicy: 'no-cache' },
  }
});

const JOURNAL_CREATED = gql`
  subscription($userId: ID!) {
    journalCreated(userId: $userId) {
      success
      message
      data { id title userId createdAt }
    }
  }
`;
const JOURNAL_UPDATED = gql`
  subscription($userId: ID!) {
    journalUpdated(userId: $userId) {
      success
      message
      data { id title userId updatedAt }
    }
  }
`;
const JOURNAL_DELETED = gql`
  subscription($userId: ID!) {
    journalDeleted(userId: $userId) {
      success
      message
      data { id title userId updatedAt }
    }
  }
`;

function subscribeAndLog(name, query) {
  const observable = client.subscribe({ query, variables: { userId } });
  const sub = observable.subscribe({
    next: (data) => {
      console.log(`\n[${name}] Subscription event received:`);
      console.dir(data, { depth: null });
    },
    error: (err) => {
      console.error(`[${name}] Subscription error:`, err);
    },
    complete: () => {
      console.log(`[${name}] Subscription complete`);
    }
  });
  return sub;
}

console.log('Subscribing to journal events for userId:', userId);
subscribeAndLog('journalCreated', JOURNAL_CREATED);
subscribeAndLog('journalUpdated', JOURNAL_UPDATED);
subscribeAndLog('journalDeleted', JOURNAL_DELETED);

// Keep the process alive
setInterval(() => {}, 1000); 