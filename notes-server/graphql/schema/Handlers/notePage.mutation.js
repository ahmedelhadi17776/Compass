const { GraphQLID, GraphQLString, GraphQLList, GraphQLBoolean } = require('graphql');
const { z } = require('zod');
const { NotePageResponseType } = require('../types/notePage.type');
const NotePage = require('../../../models/notePage.model');
const { updateBidirectionalLinks } = require('../../../utils/linkManager');
const { handleZodError, NotFoundError } = require('../../../utils/errorHandler');

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
  addNotePage: {
    type: NotePageResponseType,
    args: {
      userId: { type: GraphQLID },
      title: { type: GraphQLString },
      content: { type: GraphQLString },
      tags: { type: new GraphQLList(GraphQLString) },
      icon: { type: GraphQLString },
      linksOut: { type: new GraphQLList(GraphQLID) }
    },
    async resolve(parent, args) {
      try {
        const validatedData = CreateNotePageSchema.parse(args);
        const notePage = new NotePage(validatedData);
        await notePage.save();

        if (validatedData.linksOut.length > 0) {
          await updateBidirectionalLinks(notePage._id, validatedData.linksOut, []);
        }

        return {
          success: true,
          message: 'Note created successfully',
          data: notePage,
          errors: null
        };
      } catch (error) {
        const errors = error instanceof z.ZodError ? 
          handleZodError(error) : 
          [{ message: error.message, code: 'INTERNAL_ERROR' }];

        return {
          success: false,
          message: 'Failed to create note',
          data: null,
          errors
        };
      }
    }
  },
  updateNotePage: {
    type: NotePageResponseType,
    args: {
      id: { type: GraphQLID },
      title: { type: GraphQLString },
      content: { type: GraphQLString },
      tags: { type: new GraphQLList(GraphQLString) },
      icon: { type: GraphQLString },
      favorited: { type: GraphQLBoolean },
      linksOut: { type: new GraphQLList(GraphQLID) }
    },
    async resolve(parent, args) {
      try {
        const validatedData = UpdateNotePageSchema.parse(args);
        const { id, ...updateData } = validatedData;
        
        const note = await NotePage.findById(id);
        if (!note) throw new NotFoundError('Note');

        if (updateData.linksOut) {
          await updateBidirectionalLinks(id, updateData.linksOut, note.linksOut);
        }

        const updatedNote = await NotePage.findByIdAndUpdate(
          id,
          { $set: updateData },
          { new: true }
        );

        return {
          success: true,
          message: 'Note updated successfully',
          data: updatedNote,
          errors: null
        };
      } catch (error) {
        const errors = error instanceof z.ZodError ? 
          handleZodError(error) : 
          [{ 
            message: error.message, 
            code: error instanceof NotFoundError ? 'NOT_FOUND' : 'INTERNAL_ERROR' 
          }];

        return {
          success: false,
          message: 'Failed to update note',
          data: null,
          errors
        };
      }
    }
  },
  deleteNotePage: {
    type: NotePageResponseType,
    args: {
      id: { type: GraphQLID }
    },
    async resolve(parent, args) {
      try {
        const { id } = DeleteNotePageSchema.parse(args);
        
        const note = await NotePage.findByIdAndUpdate(
          id,
          { isDeleted: true },
          { new: true }
        );
        
        if (!note) throw new NotFoundError('Note');

        return {
          success: true,
          message: 'Note deleted successfully',
          data: note,
          errors: null
        };
      } catch (error) {
        const errors = error instanceof z.ZodError ? 
          handleZodError(error) : 
          [{ 
            message: error.message, 
            code: error instanceof NotFoundError ? 'NOT_FOUND' : 'INTERNAL_ERROR' 
          }];
          
        return {
          success: false,
          message: 'Failed to delete note',
          data: null,
          errors: errors
        };
      }
    }
  }
};

module.exports = notePageMutations; 