const { DashboardMetricsType } = require('../schemas/dashboardTypes');
const Journal = require('../../domain/journals/model');
const Note = require('../../domain/notes/model');

const dashboardMetrics = {
  type: DashboardMetricsType,
  args: { userId: { type: require('graphql').GraphQLID } },
  async resolve(parent, args, context) {
    const moodSummary = await Journal.getMoodSummary(args.userId);
    const notesCount = await Note.countDocuments({ userId: args.userId });
    const journalsCount = await Journal.countDocuments({ userId: args.userId });
    return { moodSummary, notesCount, journalsCount };
  }
};

module.exports = { dashboardMetrics }; 