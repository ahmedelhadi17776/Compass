const { GraphQLID, GraphQLString, GraphQLBoolean, GraphQLList } = require('graphql');
const { z } = require('zod');
const { 
  NotePageResponseType, 
  NotePageInput,
  getSelectedFields
} = require('../schemas/noteTypes');
const { createErrorResponse } = require('../schemas/responseTypes');
const noteService = require('../../../domain/notes/noteService');
const { ValidationError, NotFoundError, DatabaseError } = require('../../../../pkg/utils/errorHandler');
const { logger } = require('../../../../pkg/utils/logger');

// Validation for MongoDB ObjectId
const objectIdSchema = z.string()
  .regex(/^[0-9a-fA-F]{24}$/, "Invalid ID format");

// Base schema for shared fields
const BaseNotePageSchema = z.object({
  title: z.string()
    .min(1, "Title is required")
    .max(200, "Title must be less than 200 characters")
    .trim(),
  content: z.string()
    .default('')
    .transform(val => val.trim()),
  tags: z.array(
    z.string()
      .min(1, "Tags cannot be empty")
      .max(50, "Tag is too long")
      .regex(/^[a-zA-Z0-9-_]+$/, "Tags can only contain letters, numbers, hyphens and underscores")
  )
    .max(10).default([]),
  icon: z.string()
    .max(50, "Icon name or emoji too long")
    .regex(/^([a-zA-Z-]+|[\p{Emoji_Presentation}\p{Extended_Pictographic}])$/u, "Icon must be either a valid icon name (e.g., 'file-text') or a single emoji")
    .optional()
    .nullable(),
  linksOut: z.array(objectIdSchema)
    .max(100).default([])
});

// Schema for creating new notes
const CreateNotePageSchema = BaseNotePageSchema.extend({
  userId: objectIdSchema.describe("User ID is required"),
});

// Schema for updating notes
const UpdateNotePageSchema = BaseNotePageSchema.partial().extend({
  favorited: z.boolean().optional(),
  id: objectIdSchema.describe("Note ID is required"),
}).refine(data => Object.keys(data).length > 1, { // +1 because id is now required
  message: "At least one field must be provided for update"
});

// Schema for deleting notes
const DeleteNotePageSchema = z.object({
  id: objectIdSchema.describe("Note ID is required"),
});

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
          noteId: id,
          favorited
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