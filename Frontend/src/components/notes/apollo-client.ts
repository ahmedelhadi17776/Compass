import { ApolloClient, InMemoryCache, split, HttpLink } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';
import { getMainDefinition } from '@apollo/client/utilities';

// Set your test userId here or use process.env.TEST_USER_ID
const userId = '41e15c31-5dda-43d8-aea5-2d6049936c1d';

const wsLink = new GraphQLWsLink(createClient({
  url: 'ws://localhost:5000/notes/graphql',
  connectionParams: {
    'X-User-Id': userId
  }
}));

const httpLink = new HttpLink({
  uri: 'http://localhost:5000/notes/graphql',
  headers: {
    'X-User-Id': userId
  }
});

const splitLink = split(
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

export const client = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: { fetchPolicy: 'no-cache' },
    query: { fetchPolicy: 'no-cache' },
    mutate: { fetchPolicy: 'no-cache' },
  }
});

// GraphQL Operations
export const NOTE_CREATED = `
  subscription NoteCreated($userId: ID!) {
    notePageCreated(userId: $userId) {
      success
      message
      data { id title userId createdAt }
    }
  }
`;

export const NOTE_UPDATED = `
  subscription NoteUpdated($userId: ID!) {
    notePageUpdated(userId: $userId) {
      success
      message
      data { id title userId updatedAt }
    }
  }
`;

export const NOTE_DELETED = `
  subscription NoteDeleted($userId: ID!) {
    notePageDeleted(userId: $userId) {
      success
      message
      data { id title userId updatedAt }
    }
  }
`;
