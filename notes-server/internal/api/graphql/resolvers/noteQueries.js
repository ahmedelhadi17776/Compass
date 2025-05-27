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

        // Try to get from cache first
        const cachedNote = await global.redisClient.getNotePage(args.id);
        if (cachedNote) {
          return {
            success: true,
            message: 'Note retrieved from cache',
            data: cachedNote,
            errors: null
          };
        }

        const selectedFields = getSelectedFields(info);
        const note = await NotePage.findOne({
          _id: args.id,
          isDeleted: false
        })
        .select(selectedFields)
        .lean();
        
        if (!note) throw new NotFoundError('Note');

        // Cache the note
        await global.redisClient.setNotePage(args.id, note);
        
        return {
          success: true,
          message: 'Note retrieved successfully',
          data: note,
          errors: null
        };
      } catch (error) {
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
        const { userId, search, page, limit, sortField, sortOrder, filter } = args;
        
        if (!userId) {
          throw new ValidationError('User ID is required', 'userId');
        }

        // Generate cache key based on query parameters
        const cacheKey = `user:${userId}:notes:${page}:${limit}:${sortField}:${sortOrder}:${JSON.stringify(filter || {})}:${JSON.stringify(search || {})}`;

        // Try to get from cache first
        const cachedResult = await global.redisClient.get(cacheKey);
        if (cachedResult) {
          console.log('Cache hit:', cacheKey);
          return cachedResult;
        }

        const skip = (page - 1) * limit;
        const selectedFields = getSelectedFields(info);
        
        const query = { 
          userId,
          isDeleted: false
        };

        // Apply filters if provided
        if (filter) {
          if (filter.tags && filter.tags.length > 0) {
            query.tags = { $in: filter.tags };
          }
          if (typeof filter.favorited === 'boolean') {
            query.favorited = filter.favorited;
          }
          if (filter.createdAfter || filter.createdBefore) {
            query.createdAt = {};
            if (filter.createdAfter) {
              query.createdAt.$gte = new Date(filter.createdAfter);
            }
            if (filter.createdBefore) {
              query.createdAt.$lte = new Date(filter.createdBefore);
            }
          }
        }

        const sortOptions = { [sortField]: sortOrder };
        let notes;
        let totalItems;

        if (search?.query) {
          // Use MongoDB's text search with index
          query.$text = { 
            $search: search.query,
            $caseSensitive: false,
            $diacriticSensitive: false
          };
          
          notes = await NotePage.find(query)
            .select(selectedFields || 'title content tags favorited icon createdAt updatedAt userId')
            .sort({ 
              score: { $meta: 'textScore' },  // Sort by text match relevance first
              ...sortOptions 
            })
            .skip(skip)
            .limit(limit)
            .lean();
        } else {
          notes = await NotePage.find(query)
            .select(selectedFields || 'title content tags favorited icon createdAt updatedAt userId')
            .sort(sortOptions)
            .skip(skip)
            .limit(limit)
            .lean();
        }
        
        totalItems = await NotePage.countDocuments(query);

        const result = {
          success: true,
          message: 'Notes retrieved successfully',
          data: notes,
          pageInfo: {
            totalItems,
            currentPage: page,
            totalPages: Math.ceil(totalItems / limit)
          }
        };

        // Cache the result
        await global.redisClient.set(cacheKey, result);
        console.log('Cached result:', cacheKey);

        return result;
      } catch (error) {
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