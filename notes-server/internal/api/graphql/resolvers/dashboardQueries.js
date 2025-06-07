const { DashboardMetricsType } = require('../schemas/dashboardTypes');
const Journal = require('../../../domain/journals/model');
const Note = require('../../../domain/notes/model');
const RedisService = require('../../../infrastructure/cache/redisService');
const redisConfig = require('../../../infrastructure/cache/config');
const { dashboardEvents } = require('../../../infrastructure/cache/dashboardEvents');
const { logger } = require('../../../../pkg/utils/logger');

const redisClient = new RedisService(redisConfig);

const dashboardMetrics = {
  type: DashboardMetricsType,
  args: { userId: { type: require('graphql').GraphQLID } },
  async resolve(parent, args, context) {
    try {
      const userId = args.userId;

      // Check cache first
      const cacheKey = `compass:notes:dashboard:metrics:${userId}`;
      const cachedMetrics = await redisClient.get(cacheKey);

      if (cachedMetrics) {
        logger.debug('Returning cached dashboard metrics', { userId });
        return JSON.parse(cachedMetrics);
      }

      logger.info('Generating dashboard metrics', { userId });

      // Get mood summary from journals
      const moodSummary = await Journal.getMoodSummary(userId);

      // Count notes and journals
      const notesCount = await Note.countDocuments({ userId, isDeleted: false });
      const journalsCount = await Journal.countDocuments({ userId, isDeleted: false });

      // Get recent notes (last 5)
      const recentNotes = await Note.find({ userId, isDeleted: false })
        .sort({ updatedAt: -1 })
        .limit(5)
        .select('title content updatedAt')
        .lean();

      // Get recent journals (last 5)
      const recentJournals = await Journal.find({ userId, isDeleted: false })
        .sort({ date: -1 })
        .limit(5)
        .select('title content date mood')
        .lean();

      // Get tag distribution
      const tagCounts = await Note.aggregate([
        { $match: { userId, isDeleted: false } },
        { $unwind: "$tags" },
        { $group: { _id: "$tags", count: { $sum: 1 } } },
        { $sort: { count: -1 } },
        { $limit: 10 }
      ]);

      // Parse mood summary for mood distribution
      let moodDistribution = {};
      try {
        if (moodSummary) {
          moodDistribution = JSON.parse(moodSummary);
        }
      } catch (error) {
        logger.warn('Failed to parse mood summary', { error: error.message });
      }

      const metrics = {
        moodSummary,
        notesCount,
        journalsCount,
        recentNotes,
        recentJournals,
        tagCounts,
        moodDistribution,
        timestamp: new Date().toISOString()
      };

      // Cache the metrics
      await redisClient.set(cacheKey, JSON.stringify(metrics), 300); // Cache for 5 minutes

      // Publish metrics update event
      await dashboardEvents.publishMetricsUpdate(userId, null, metrics);

      return metrics;
    } catch (error) {
      logger.error('Error fetching dashboard metrics', { error: error.message, userId: args.userId });
      throw new Error('Failed to fetch dashboard metrics');
    }
  }
};

module.exports = { dashboardMetrics };