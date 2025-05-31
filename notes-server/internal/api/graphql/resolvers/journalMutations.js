const { GraphQLID } = require('graphql');
const { 
  JournalResponseType, 
  JournalInput,
  getSelectedFields
} = require('../schemas/journalTypes');
const journalService = require('../../../domain/journals/journalService');
const { ValidationError, NotFoundError, DatabaseError } = require('../../../../pkg/utils/errorHandler');
const { logger } = require('../../../../pkg/utils/logger');

const journalMutations = {
  createJournal: {
    type: JournalResponseType,
    args: { 
      input: { type: JournalInput }
    },
    async resolve(parent, args, context, info) {
      try {
        const { input } = args;
        const selectedFields = getSelectedFields(info);
        const currentUserId = context.user && context.user.id;
        const inputWithUser = { ...input, userId: currentUserId };
        const savedJournal = await journalService.createJournal(inputWithUser, selectedFields);
        
        return {
          success: true,
          message: 'Journal entry created successfully',
          data: savedJournal,
          errors: null
        };
      } catch (error) {
        logger.error('Error in createJournal', {
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
  updateJournal: {
    type: JournalResponseType,
    args: { 
      id: { type: GraphQLID },
      input: { type: JournalInput }
    },
    async resolve(parent, args, context, info) {
      try {
        const { id, input } = args;
        const selectedFields = getSelectedFields(info);
        const currentUserId = context.user && context.user.id;
        const inputWithUser = { ...input, userId: currentUserId };
        const updatedJournal = await journalService.updateJournal(id, inputWithUser, selectedFields);
        
        return {
          success: true,
          message: 'Journal entry updated successfully',
          data: updatedJournal,
          errors: null
        };
      } catch (error) {
        logger.error('Error in updateJournal', {
          error: error.message,
          stack: error.stack,
          journalId: args.id,
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
  deleteJournal: {
    type: JournalResponseType,
    args: { id: { type: GraphQLID } },
    async resolve(parent, args, context, info) {
      try {
        const { id } = args;
        const selectedFields = getSelectedFields(info);
        
        const deletedJournal = await journalService.deleteJournal(id, selectedFields);
        
        return {
          success: true,
          message: 'Journal entry permanently deleted successfully',
          data: deletedJournal,
          errors: null
        };
      } catch (error) {
        logger.error('Error in deleteJournal', {
          error: error.message,
          stack: error.stack,
          journalId: args.id
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
  archiveJournal: {
    type: JournalResponseType,
    args: { id: { type: GraphQLID } },
    async resolve(parent, args, context, info) {
      try {
        const { id } = args;
        const selectedFields = getSelectedFields(info);
        
        const archivedJournal = await journalService.archiveJournal(id, selectedFields);
        
        return {
          success: true,
          message: 'Journal entry archived successfully',
          data: archivedJournal,
          errors: null
        };
      } catch (error) {
        logger.error('Error in archiveJournal', {
          error: error.message,
          stack: error.stack,
          journalId: args.id
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
  }
};

module.exports = journalMutations; 