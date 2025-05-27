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
const Journal = require('../../../domain/journals/model');
const { createResponseType } = require('./responseTypes');

// Enum for mood values
const MoodEnum = new GraphQLEnumType({
  name: 'Mood',
  values: {
    HAPPY: { value: 'happy' },
    SAD: { value: 'sad' },
    ANGRY: { value: 'angry' },
    NEUTRAL: { value: 'neutral' },
    EXCITED: { value: 'excited' },
    ANXIOUS: { value: 'anxious' },
    TIRED: { value: 'tired' },
    GRATEFUL: { value: 'grateful' }
  }
});

// Input type for journal mutations
const JournalInput = new GraphQLInputObjectType({
  name: 'JournalInput',
  fields: {
    userId: { 
      type: GraphQLID,
      description: 'ID of the user who owns the journal'
    },
    title: { 
      type: GraphQLString,
      description: 'Title of the journal (max 200 characters)'
    },
    date: {
      type: GraphQLString,
      description: 'Date of the journal'
    },
    content: { 
      type: GraphQLString,
      description: 'Content of the journal (max 10000 characters)'
    },
    mood: {
      type: MoodEnum,
      description: 'Mood associated with the journal'
    },
    tags: { 
      type: new GraphQLList(GraphQLString),
      description: 'List of tags (max 10 tags, each max 50 characters)'
    },
    aiPromptUsed: {
      type: GraphQLString,
      description: 'AI prompt used to generate the journal'
    },
    aiGenerated: {
      type: GraphQLBoolean,
      description: 'Whether the journal is AI generated'
    },
    archived: {
      type: GraphQLBoolean,
      description: 'Whether the journal is archived'
    },
    wordCount: {
      type: GraphQLInt,
      description: 'Word count of the journal'
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

const JournalSortFieldEnum = new GraphQLEnumType({
  name: 'JournalSortField',
  description: 'Fields by which journals can be sorted',
  values: {
    DATE: { value: 'date' },
    CREATED_AT: { value: 'createdAt' },
    UPDATED_AT: { value: 'updatedAt' },
    TITLE: { value: 'title' },
    WORD_COUNT: { value: 'wordCount' },
    MOOD: { value: 'mood' }
  }
});

const SortOrderEnum = new GraphQLEnumType({
  name: 'JournalSortOrder',
  values: {
    ASC: { value: 1 },
    DESC: { value: -1 }
  }
});

const JournalFilterInput = new GraphQLInputObjectType({
  name: 'JournalFilter',
  description: 'Filters for journals',
  fields: {
    wordCountMin: { type: GraphQLInt },
    wordCountMax: { type: GraphQLInt },
    aiGenerated: { type: GraphQLBoolean },
    tags: { type: new GraphQLList(GraphQLString) },
    mood: { type: MoodEnum },
    archived: { type: GraphQLBoolean },
    dateFrom: { 
      type: GraphQLString,
      description: 'Filter journals from this date (inclusive)'
    },
    dateTo: { 
      type: GraphQLString,
      description: 'Filter journals to this date (inclusive)'
    }
  }
});

// Helper function to get selected fields from GraphQL query
const getSelectedFields = (info) => {
  const selections = info.fieldNodes[0].selectionSet.selections;
  return selections
    .find(selection => selection.name.value === 'data')
    ?.selectionSet.selections
    .map(selection => selection.name.value)
    .join(' ');
};

const JournalType = new GraphQLObjectType({
  name: 'Journal',
  fields: () => ({
    _id: { type: GraphQLID },
    userId: { type: GraphQLID },
    title: { type: GraphQLString },
    date: { type: GraphQLString },
    content: { type: GraphQLString },
    mood: { type: MoodEnum },
    tags: { type: new GraphQLList(GraphQLString) },
    aiPromptUsed: { type: GraphQLString },
    aiGenerated: { type: GraphQLBoolean },
    archived: { type: GraphQLBoolean },
    wordCount: { type: GraphQLInt },
    createdAt: { type: GraphQLString },
    updatedAt: { type: GraphQLString }
  })
});

// Create response types for single and list responses
const JournalResponseType = createResponseType(JournalType, 'Journal');
const JournalListResponseType = createResponseType(new GraphQLList(JournalType), 'JournalList');

module.exports = { 
  JournalType,
  JournalResponseType,
  JournalListResponseType,
  MoodEnum,
  JournalSortFieldEnum,
  SortOrderEnum,
  JournalFilterInput,
  JournalInput,
  PaginationInput,
  getSelectedFields
}; 