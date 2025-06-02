import { gql } from '@apollo/client';

export const NOTE_CREATED_SUBSCRIPTION = gql`
  subscription($userId: ID!) {
    notePageCreated(userId: $userId) {
      success
      message
      data { id title userId createdAt }
    }
  }
`;

export const NOTE_UPDATED_SUBSCRIPTION = gql`
  subscription($userId: ID!) {
    notePageUpdated(userId: $userId) {
      success
      message
      data { id title userId updatedAt }
    }
  }
`;

export const NOTE_DELETED_SUBSCRIPTION = gql`
  subscription($userId: ID!) {
    notePageDeleted(userId: $userId) {
      success
      message
      data { id title userId updatedAt }
    }
  }
`;

export const GET_NOTES = gql`
  query GetNotes($userId: ID!, $page: Int!) {
    notePages(userId: $userId, page: $page) {
      success
      message
      data {
        id
        title
        content
        userId
        tags
        favorited
        createdAt
        updatedAt
      }
      pageInfo {
        totalPages
        totalItems
        currentPage
      }
    }
  }
`;

export const CREATE_NOTE = gql`
  mutation CreateNote($input: NotePageInput!) {
    createNotePage(input: $input) {
      success
      message
      data {
        id
        title
        content
        userId
        tags
        favorited
        createdAt
        updatedAt
      }
    }
  }
`;

export const UPDATE_NOTE = gql`
  mutation UpdateNote($id: ID!, $input: NotePageInput!) {
    updateNotePage(id: $id, input: $input) {
      success
      message
      data {
        id
        title
        content
        userId
        tags
        favorited
        updatedAt
      }
    }
  }
`;

export const DELETE_NOTE = gql`
  mutation DeleteNote($id: ID!) {
    deleteNotePage(id: $id) {
      success
      message
      data {
        id
      }
    }
  }
`; 