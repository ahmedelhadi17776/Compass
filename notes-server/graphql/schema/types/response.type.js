const { 
  GraphQLObjectType, 
  GraphQLString, 
  GraphQLBoolean, 
  GraphQLList,
  GraphQLInt
} = require('graphql');

const ErrorType = new GraphQLObjectType({
  name: 'Error',
  fields: {
    message: { type: GraphQLString },
    field: { type: GraphQLString },
    code: { type: GraphQLString }
  }
});

const PageInfoType = new GraphQLObjectType({
  name: 'PageInfo',
  fields: {
    hasNextPage: { type: GraphQLBoolean },
    hasPreviousPage: { type: GraphQLBoolean },
    totalPages: { type: GraphQLInt },
    totalItems: { type: GraphQLInt },
    currentPage: { type: GraphQLInt }
  }
});

const createResponseType = (dataType, name) => {
  return new GraphQLObjectType({
    name: `${name}Response`,
    fields: {
      success: { type: GraphQLBoolean },
      message: { type: GraphQLString },
      data: { type: dataType },
      errors: { type: new GraphQLList(ErrorType) },
      pageInfo: { type: PageInfoType }
    }
  });
};

module.exports = { createResponseType, PageInfoType, ErrorType }; 