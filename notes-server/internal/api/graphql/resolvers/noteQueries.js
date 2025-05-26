const { GraphQLID, GraphQLString, GraphQLInt, GraphQLInputObjectType, GraphQLBoolean } = require('graphql');
const { 
  NotePageResponseType, 
  NotePageListResponseType,
  NoteSortFieldEnum,
  SortOrderEnum,
  NoteFilterInput
} = require('../schemas/noteTypes');
const NotePage = require('../../../domain/notes/model');
const { NotFoundError } = require('../../../../pkg/utils/errorHandler');

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
    async resolve(parent, args, context) {
      try {
        const note = await NotePage.findOne({
          _id: args.id,
          isDeleted: false
        });
        
        if (!note) throw new NotFoundError('Note');
        
        return {
          success: true,
          message: 'Note retrieved successfully',
          data: note,
          errors: null
        };
      } catch (error) {
        return {
          success: false,
          message: error.message,
          data: null,
          errors: [{
            message: error.message,
            code: error instanceof NotFoundError ? 'NOT_FOUND' : 'INTERNAL_ERROR'
          }]
        };
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
    async resolve(parent, args) {
      try {
        const { userId, search, page, limit, sortField, sortOrder, filter } = args;
        const skip = (page - 1) * limit;
        
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

        let notes;
        let totalItems;
        const sortOptions = { [sortField]: sortOrder };

        if (search?.query) {
          // Use MongoDB's text search with index
          query.$text = { 
            $search: search.query,
            $caseSensitive: false,
            $diacriticSensitive: false
          };
          
          notes = await NotePage.find(query)
            .select('title content tags favorited icon createdAt updatedAt userId')
            .sort({ 
              score: { $meta: 'textScore' },  // Sort by text match relevance first
              ...sortOptions 
            })
            .skip(skip)
            .limit(limit);
        } else {
          notes = await NotePage.find(query)
            .select('title content tags favorited icon createdAt updatedAt userId')
            .sort(sortOptions)
            .skip(skip)
            .limit(limit);
        }
        
        totalItems = await NotePage.countDocuments(query);
        const totalPages = Math.ceil(totalItems / limit);

        return {
          success: true,
          message: 'Notes retrieved successfully',
          data: notes,
          pageInfo: {
            hasNextPage: page < totalPages,
            hasPreviousPage: page > 1,
            totalPages,
            totalItems,
            currentPage: page
          }
        };
      } catch (error) {
        return {
          success: false,
          message: error.message,
          data: [],
          errors: [{
            message: error.message,
            code: 'INTERNAL_ERROR'
          }]
        };
      }
    }
  }
};

module.exports = notePageQueries; 