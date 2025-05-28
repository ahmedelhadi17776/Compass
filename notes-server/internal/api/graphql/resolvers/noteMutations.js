const { GraphQLID, GraphQLBoolean } = require('graphql');
const { 
  NotePageResponseType, 
  NotePageInput,
  getSelectedFields
} = require('../schemas/noteTypes');
const noteService = require('../../../domain/notes/noteService');
const { ValidationError, NotFoundError, DatabaseError, BaseError } = require('../../../../pkg/utils/errorHandler');
const { logger } = require('../../../../pkg/utils/logger');

const notePageMutations = {
  createNotePage: {
    type: NotePageResponseType,
    args: { 
      input: { type: NotePageInput }
    },
    async resolve(parent, args, context, info) {
      try {
        const { input } = args;
        const selectedFields = getSelectedFields(info);
        
        const savedNote = await noteService.createNote(input, selectedFields);
        
        return {
          success: true,
          message: 'Note created successfully',
          data: savedNote,
          errors: null
        };
      } catch (error) {
        logger.error('Error in createNotePage', {
          error: error.message,
          stack: error.stack,
          input: args.input
        });
        return {
          success: false,
          message: error.message,
          data: null,
          errors: [{
            message: error.message,
            field: error.field,
            code: error instanceof ValidationError ? 'VALIDATION_ERROR' : 
                  error instanceof DatabaseError ? 'DATABASE_ERROR' : 'INTERNAL_ERROR'
          }]
        };
      }
    }
  },
  updateNotePage: {
    type: NotePageResponseType,
    args: { 
      id: { type: GraphQLID },
      input: { type: NotePageInput }
    },
    async resolve(parent, args, context, info) {
      try {
        const { id, input } = args;
        const selectedFields = getSelectedFields(info);
        
        const updatedNote = await noteService.updateNote(id, input, selectedFields);
        
        return {
          success: true,
          message: 'Note updated successfully',
          data: updatedNote,
          errors: null
        };
      } catch (error) {
        logger.error('Error in updateNotePage', {
          error: error.message,
          stack: error.stack,
          noteId: args.id,
          input: args.input
        });
        return {
          success: false,
          message: error.message,
          data: null,
          errors: [{
            message: error.message,
            field: error.field,
            code: error instanceof ValidationError ? 'VALIDATION_ERROR' : 
                  error instanceof NotFoundError ? 'NOT_FOUND' :
                  error instanceof DatabaseError ? 'DATABASE_ERROR' : 'INTERNAL_ERROR'
          }]
        };
      }
    }
  },
  deleteNotePage: {
    type: NotePageResponseType,
    args: { id: { type: GraphQLID } },
    async resolve(parent, args, context, info) {
      try {
        const { id } = args;
        const selectedFields = getSelectedFields(info);
        
        const deletedNote = await noteService.deleteNote(id, selectedFields);
        
        return {
          success: true,
          message: 'Note deleted successfully',
          data: deletedNote,
          errors: null
        };
      } catch (error) {
        logger.error('Error in deleteNotePage', {
          error: error.message,
          stack: error.stack,
          noteId: args.id
        });
        return {
          success: false,
          message: error.message,
          data: null,
          errors: [{
            message: error.message,
            field: error.field,
            code: error instanceof ValidationError ? 'VALIDATION_ERROR' : 
                  error instanceof NotFoundError ? 'NOT_FOUND' : 'INTERNAL_ERROR'
          }]
        };
      }
    }
  },
  toggleFavorite: {
    type: NotePageResponseType,
    args: { 
      id: { type: GraphQLID },
      favorited: { type: GraphQLBoolean }
    },
    async resolve(parent, args, context, info) {
      try {
        const { id, favorited } = args;
        const selectedFields = getSelectedFields(info);
        
        const updatedNote = await noteService.toggleFavorite(id, favorited, selectedFields);
        
        return {
          success: true,
          message: `Note ${favorited ? 'favorited' : 'unfavorited'} successfully`,
          data: updatedNote,
          errors: null
        };
      } catch (error) {
        logger.error('Error in toggleFavorite', {
          error: error.message,
          stack: error.stack,
          noteId: args.id,
          favorited: args.favorited
        });

        if (error instanceof BaseError) {
          throw error;
        }
        throw new DatabaseError(`Failed to toggle favorite status: ${error.message}`);
      }
    }
  }
};

module.exports = notePageMutations; 