const { GraphQLID, GraphQLString, GraphQLBoolean, GraphQLList } = require('graphql');
const { z } = require('zod');
const { 
  NotePageResponseType, 
  NotePageInput,
  getSelectedFields
} = require('../schemas/noteTypes');
const { createErrorResponse } = require('../schemas/responseTypes');
const NotePage = require('../../../domain/notes/model');
const { updateBidirectionalLinks, validateLinks } = require('../../../domain/notes/linkService');
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
        logger.debug('Creating note page', { input });
        
        if (!input.userId) {
          throw new ValidationError('User ID is required', 'userId');
        }

        if (!input.title?.trim()) {
          throw new ValidationError('Title is required', 'title');
        }

        // Validate links if provided
        if (input.linksOut && input.linksOut.length > 0) {
          try {
            await validateLinks(input.linksOut);
          } catch (error) {
            throw new ValidationError(error.message, 'linksOut');
          }
        }

        const note = new NotePage(input);
        await note.save();
        logger.info('Note page created', { noteId: note._id });

        // Update bidirectional links if any
        if (input.linksOut?.length > 0) {
          await updateBidirectionalLinks(note._id, [], input.linksOut);
          logger.debug('Bidirectional links updated', { 
            noteId: note._id,
            linksOut: input.linksOut
          });
        }

        const selectedFields = getSelectedFields(info);
        const savedNote = await NotePage.findById(note._id)
          .select(selectedFields)
          .lean();

        const result = {
          success: true,
          message: 'Note created successfully',
          data: savedNote,
          errors: null
        };

        // Cache the new note
        await global.redisClient.set(
          `note:${note._id}`,
          savedNote
        );

        // Invalidate user's note list cache
        await global.redisClient.clearByPattern(`user:${input.userId}:notes:*`);

        logger.info('Note page creation completed', { 
          noteId: note._id,
          userId: input.userId
        });

        return result;
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
        logger.debug('Updating note page', { noteId: id, input });

        if (!id) {
          throw new ValidationError('Note ID is required', 'id');
        }

        const existingNote = await NotePage.findById(id);
        if (!existingNote) {
          throw new NotFoundError('Note');
        }

        // Validate links if provided
        if (input.linksOut?.length > 0) {
          await validateLinks(input.linksOut);
        }

        // Update note
        Object.assign(existingNote, input);
        await existingNote.save();
        logger.info('Note page updated', { noteId: id });

        // Update bidirectional links if changed
        if (input.linksOut) {
          await updateBidirectionalLinks(id, existingNote.linksOut, input.linksOut);
          logger.debug('Bidirectional links updated', { 
            noteId: id,
            oldLinks: existingNote.linksOut,
            newLinks: input.linksOut
          });
        }

        const selectedFields = getSelectedFields(info);
        const updatedNote = await NotePage.findById(id)
          .select(selectedFields)
          .lean();

        // Update cache
        await global.redisClient.setNotePage(id, updatedNote);
        
        // Invalidate related caches
        await Promise.all([
          global.redisClient.clearByPattern(`user:${existingNote.userId}:notes:*`),
          ...existingNote.linksOut.map(linkedId => 
            global.redisClient.invalidateCache('note', linkedId)
          ),
          ...existingNote.linksIn.map(linkedId => 
            global.redisClient.invalidateCache('note', linkedId)
          )
        ]);

        logger.info('Note page update completed', { 
          noteId: id,
          userId: existingNote.userId
        });

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
        logger.debug('Deleting note page', { noteId: id });

        if (!id) {
          throw new ValidationError('Note ID is required', 'id');
        }

        const note = await NotePage.findById(id);
        if (!note) {
          throw new NotFoundError('Note');
        }

        // Soft delete
        note.isDeleted = true;
        await note.save();
        logger.info('Note page marked as deleted', { noteId: id });

        // Remove bidirectional links
        if (note.linksOut?.length > 0) {
          await updateBidirectionalLinks(id, note.linksOut, []);
          logger.debug('Bidirectional links removed', { 
            noteId: id,
            linksOut: note.linksOut
          });
        }

        const selectedFields = getSelectedFields(info);
        const deletedNote = await NotePage.findById(id)
          .select(selectedFields)
          .lean();

        // Invalidate all related caches
        await Promise.all([
          global.redisClient.invalidateCache('note', id),
          global.redisClient.clearByPattern(`user:${note.userId}:notes:*`),
          ...note.linksOut.map(linkedId => 
            global.redisClient.invalidateCache('note', linkedId)
          ),
          ...note.linksIn.map(linkedId => 
            global.redisClient.invalidateCache('note', linkedId)
          )
        ]);

        logger.info('Note page deletion completed', { 
          noteId: id,
          userId: note.userId
        });

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
        logger.debug('Toggling favorite status', { noteId: id, favorited });

        if (!id) {
          throw new ValidationError('Note ID is required', 'id');
        }

        if (typeof favorited !== 'boolean') {
          throw new ValidationError('Favorite status is required', 'favorited');
        }

        const note = await NotePage.findById(id);
        if (!note) {
          throw new NotFoundError('Note');
        }

        note.favorited = favorited;
        await note.save();

        // Update cache
        if (context.redisClient) {
          try {
            await context.redisClient.setNotePage(id, note.toObject());
          } catch (cacheError) {
            logger.warn('Failed to update note cache', { 
              error: cacheError.message,
              noteId: id 
            });
          }
        }

        logger.info('Note favorite status updated', { noteId: id, favorited });

        const selectedFields = getSelectedFields(info);
        const updatedNote = await NotePage.findById(id)
          .select(selectedFields)
          .lean();

        // Invalidate user's note list cache
        await global.redisClient.clearByPattern(`user:${note.userId}:notes:*`);

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