const { 
  GraphQLObjectType, 
  GraphQLString, 
  GraphQLID, 
  GraphQLList, 
  GraphQLBoolean,
  GraphQLEnumType,
  GraphQLInputObjectType
} = require('graphql');
const NotePage = require('../../../domain/notes/model');
const { createResponseType } = require('./responseTypes');

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

const NotePageType = new GraphQLObjectType({
  name: 'NotePage',
  fields: () => ({
    id: { type: GraphQLID },
    userId: { type: GraphQLID },
    title: { type: GraphQLString },
    content: { type: GraphQLString },
    linksOut: { 
      type: new GraphQLList(NotePageType),
      resolve(parent) {
        return NotePage.find({ _id: { $in: parent.linksOut } });
      }
    },
    linksIn: { 
      type: new GraphQLList(NotePageType),
      resolve(parent) {
        return NotePage.find({ _id: { $in: parent.linksIn } });
      }
    },
    entities: { type: new GraphQLList(EntityType) },
    tags: { type: new GraphQLList(GraphQLString) },
    isDeleted: { type: GraphQLBoolean },
    favorited: { type: GraphQLBoolean },
    icon: { type: GraphQLString },
    createdAt: { type: GraphQLString },
    updatedAt: { type: GraphQLString }
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
  NoteFilterInput
}; 