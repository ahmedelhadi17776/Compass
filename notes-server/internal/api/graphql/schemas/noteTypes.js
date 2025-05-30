const { 
  GraphQLObjectType, 
  GraphQLString, 
  GraphQLID, 
  GraphQLList, 
  GraphQLBoolean,
  GraphQLEnumType,
  GraphQLInputObjectType,
  GraphQLInt
} = require('graphql');
const NotePage = require('../../../domain/notes/model');
const { createResponseType } = require('./responseTypes');

// Permission enums and input must be defined before NotePageInput
const PermissionLevelEnum = new GraphQLEnumType({
  name: 'PermissionLevel',
  values: {
    VIEW: { value: 'view' },
    EDIT: { value: 'edit' },
    COMMENT: { value: 'comment' }
  }
});

const PermissionInput = new GraphQLInputObjectType({
  name: 'PermissionInput',
  fields: {
    userId: { type: GraphQLID },
    level: { type: PermissionLevelEnum }
  }
});

// Output type for permissions
const PermissionType = new GraphQLObjectType({
  name: 'Permission',
  fields: {
    userId: { type: GraphQLID },
    level: { type: PermissionLevelEnum }
  }
});

// Input types for better mutation handling
const NotePageInput = new GraphQLInputObjectType({
  name: 'NotePageInput',
  fields: {
    userId: { 
      type: GraphQLID,
      description: '[IGNORED] ID of the user who owns the note. Always set from backend.'
    },
    title: { 
      type: GraphQLString,
      description: 'Title of the note (max 200 characters)'
    },
    content: { 
      type: GraphQLString,
      description: 'Content of the note (max 10000 characters)'
    },
    tags: { 
      type: new GraphQLList(GraphQLString),
      description: 'List of tags (max 10 tags, each max 50 characters)'
    },
    icon: { 
      type: GraphQLString,
      description: 'Icon name or emoji (max 50 characters)'
    },
    favorited: {
      type: GraphQLBoolean,
      description: 'Whether the note is favorited'
    },
    linksOut: { 
      type: new GraphQLList(GraphQLID),
      description: 'List of note IDs this note links to'
    },
    sharedWith: {
      type: new GraphQLList(GraphQLID),
      description: 'List of user IDs the note is shared with'
    },
    permissions: {
      type: new GraphQLList(PermissionInput),
      description: 'List of permissions for users'
    }
  }
});

const PaginationInput = new GraphQLInputObjectType({
  name: 'PaginationInput',
  fields: {
    page: { type: GraphQLInt, defaultValue: 1 },
    limit: { type: GraphQLInt, defaultValue: 10 }
  }
});

const NoteSortFieldEnum = new GraphQLEnumType({
  name: 'NoteSortField',
  values: {
    CREATED_AT: { value: 'createdAt' },
    UPDATED_AT: { value: 'updatedAt' },
    TITLE: { value: 'title' }
  }
});

const SortOrderEnum = new GraphQLEnumType({
  name: 'SortOrder',
  values: {
    ASC: { value: 1 },
    DESC: { value: -1 }
  }
});

const NoteFilterInput = new GraphQLInputObjectType({
  name: 'NoteFilter',
  fields: {
    tags: { type: new GraphQLList(GraphQLString) },
    favorited: { type: GraphQLBoolean },
    createdAfter: { type: GraphQLString },
    createdBefore: { type: GraphQLString }
  }
});

const EntityType = new GraphQLObjectType({
  name: 'Entity',
  fields: {
    type: { type: GraphQLString },
    refId: { type: GraphQLID }
  }
});

// Helper function to get selected fields from GraphQL query
const getSelectedFields = (info) => {
  try {
    const selections = info.fieldNodes[0].selectionSet.selections;
    const dataSelection = selections.find(selection => selection.name.value === 'data');
    if (dataSelection && dataSelection.selectionSet) {
      return dataSelection.selectionSet.selections.map(sel => sel.name.value).join(' ');
    }
    // If 'data' is not present, fallback to default fields
    return 'title content tags favorited icon createdAt updatedAt userId';
  } catch (e) {
    // Fallback in case of any error
    return 'title content tags favorited icon createdAt updatedAt userId';
  }
};

const NotePageType = new GraphQLObjectType({
  name: 'NotePage',
  fields: () => ({
    id: {
      type: GraphQLID,
      description: 'String ID for GraphQL compatibility',
      resolve: (parent) => parent._id ? parent._id.toString() : null
    },
    _id: { type: GraphQLID },
    userId: { type: GraphQLID },
    title: { type: GraphQLString },
    content: { type: GraphQLString },
    linksOut: { 
      type: new GraphQLList(NotePageType),
      resolve: async (parent, args, context, info) => {
        if (!info.fieldNodes[0].selectionSet) return [];
        const selectedFields = getSelectedFields(info);
        return NotePage.find({ _id: { $in: parent.linksOut } })
          .select(selectedFields || 'title content tags favorited icon')
          .lean();
      }
    },
    linksIn: { 
      type: new GraphQLList(NotePageType),
      resolve: async (parent, args, context, info) => {
        if (!info.fieldNodes[0].selectionSet) return [];
        const selectedFields = getSelectedFields(info);
        return NotePage.find({ _id: { $in: parent.linksIn } })
          .select(selectedFields || 'title content tags favorited icon')
          .lean();
      }
    },
    entities: { type: new GraphQLList(EntityType) },
    tags: { type: new GraphQLList(GraphQLString) },
    isDeleted: { type: GraphQLBoolean },
    favorited: { type: GraphQLBoolean },
    icon: { type: GraphQLString },
    createdAt: { type: GraphQLString },
    updatedAt: { type: GraphQLString },
    linkedNotesCount: {
      type: GraphQLInt,
      resolve: (parent) => (parent.linksOut?.length || 0) + (parent.linksIn?.length || 0)
    },
    sharedWith: {
      type: new GraphQLList(GraphQLID),
      description: 'List of user IDs the note is shared with'
    },
    permissions: {
      type: new GraphQLList(PermissionType),
      description: 'List of permissions for users'
    }
  })
});

// Create response types for single and list responses
const NotePageResponseType = createResponseType(NotePageType, 'NotePage');
const NotePageListResponseType = createResponseType(new GraphQLList(NotePageType), 'NotePageList');

module.exports = { 
  NotePageType,
  NotePageResponseType,
  NotePageListResponseType,
  NoteSortFieldEnum,
  SortOrderEnum,
  NoteFilterInput,
  NotePageInput,
  PaginationInput,
  getSelectedFields
}; 