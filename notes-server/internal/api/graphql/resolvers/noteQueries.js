const { GraphQLID, GraphQLString, GraphQLInt, GraphQLInputObjectType, GraphQLBoolean } = require('graphql');
const { 
  NotePageResponseType, 
  NotePageListResponseType,
  NoteSortFieldEnum,
  SortOrderEnum,
  NoteFilterInput,
  getSelectedFields
} = require('../schemas/noteTypes');
const { createErrorResponse, createPaginatedResponse } = require('../schemas/responseTypes');
const NotePage = require('../../../domain/notes/model');
const { NotFoundError, ValidationError } = require('../../../../pkg/utils/errorHandler');
const { logger } = require('../../../../pkg/utils/logger');
const noteService = require('../../../domain/notes/noteService');

// Search input type for more granular search control
const NoteSearchInput = new GraphQLInputObjectType({
  name: 'NoteSearch',
  fields: {
    query: { type: GraphQLString },
  }
});

const notePageQueries = {
  notePage: {
    type: NotePageResponseType,
    args: { id: { type: GraphQLID } },
    async resolve(parent, args, context, info) {
      try {
        if (!args.id) {
          throw new ValidationError('Note ID is required', 'id');
        }
        const selectedFields = getSelectedFields(info);
        const note = await noteService.getNote(args.id, selectedFields);
        return {
          success: true,
          message: 'Note retrieved successfully',
          data: note,
          errors: null
        };
      } catch (error) {
        logger.error('Error in notePage query', {
          error: error.message,
          stack: error.stack,
          noteId: args.id
        });
        return createErrorResponse(
          error.message,
          [{
            message: error.message,
            field: error.field,
            code: error instanceof ValidationError ? 'VALIDATION_ERROR' : 
                  error instanceof NotFoundError ? 'NOT_FOUND' : 'INTERNAL_ERROR'
          }]
        );
      }
    }
  },
  notePages: {
    type: NotePageListResponseType,
    args: { 
      userId: { type: GraphQLID },
      search: { type: NoteSearchInput },
      page: { type: GraphQLInt, defaultValue: 1 },
      limit: { type: GraphQLInt, defaultValue: 10 },
      sortField: { type: NoteSortFieldEnum, defaultValue: 'createdAt' },
      sortOrder: { type: SortOrderEnum, defaultValue: -1 },
      filter: { type: NoteFilterInput }
    },
    async resolve(parent, args, context, info) {
      try {
        const selectedFields = getSelectedFields(info);
        const result = await noteService.getNotes(args, selectedFields);
        return result;
      } catch (error) {
        logger.error('Error in notePages query', {
          error: error.message,
          stack: error.stack,
          userId: args.userId,
          page: args.page,
          limit: args.limit
        });
        return createErrorResponse(
          error.message,
          [{
            message: error.message,
            field: error.field,
            code: error instanceof ValidationError ? 'VALIDATION_ERROR' : 'INTERNAL_ERROR'
          }]
        );
      }
    }
  }
};

module.exports = notePageQueries; 