const { GraphQLObjectType, GraphQLInt, GraphQLString } = require('graphql');

const DashboardMetricsType = new GraphQLObjectType({
  name: 'DashboardMetrics',
  fields: {
    moodSummary: { type: GraphQLString },
    notesCount: { type: GraphQLInt },
    journalsCount: { type: GraphQLInt }
  }
});

module.exports = { DashboardMetricsType }; 