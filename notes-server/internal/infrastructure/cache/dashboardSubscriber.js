const Redis = require('ioredis');
const { logger } = require('../../../pkg/utils/logger');
const redisConfig = require('./config');
const RedisService = require('./redisService');

// Dashboard event types
const EVENT_TYPES = {
  METRICS_UPDATE: 'metrics_update',
  CACHE_INVALIDATE: 'cache_invalidate'
};

// Dashboard event channel - must match the Go backend
const DASHBOARD_EVENT_CHANNEL = 'dashboard:events';

const redisClient = new RedisService(redisConfig);

class DashboardEventSubscriber {
  constructor() {
    this.subscriber = new Redis({
      host: redisConfig.host || 'localhost',
      port: redisConfig.port || 6380,
      password: redisConfig.password || '',
      db: redisConfig.db || 2
    });

    this.subscriber.on('error', (error) => {
      logger.error('Redis subscriber error:', { error: error.message });
    });

    this.subscriber.on('connect', () => {
      logger.info('Redis subscriber connected');
    });

    this.isSubscribed = false;
  }

  async subscribe() {
    if (this.isSubscribed) {
      logger.info('Already subscribed to dashboard events');
      return;
    }

    try {
      await this.subscriber.subscribe(DASHBOARD_EVENT_CHANNEL);
      this.isSubscribed = true;

      this.subscriber.on('message', async (channel, message) => {
        if (channel === DASHBOARD_EVENT_CHANNEL) {
          try {
            const event = JSON.parse(message);
            logger.info('Received dashboard event', {
              eventType: event.event_type,
              userId: event.user_id
            });

            // Handle different event types
            if (!event.user_id) {
              logger.warn('Dashboard event missing user_id', { event });
              return;
            }

            switch (event.event_type) {
              case EVENT_TYPES.METRICS_UPDATE:
                await this.handleMetricsUpdate(event.user_id);
                break;
              case EVENT_TYPES.CACHE_INVALIDATE:
                await this.handleCacheInvalidate(event.user_id);
                break;
              default:
                logger.warn('Unknown dashboard event type', { eventType: event.event_type });
                // Default behavior: invalidate metrics cache
                await this.handleMetricsUpdate(event.user_id);
            }
          } catch (error) {
            logger.error('Error processing dashboard event', { error: error.message });
          }
        }
      });

      logger.info('Subscribed to dashboard events');
    } catch (error) {
      logger.error('Failed to subscribe to dashboard events', { error: error.message });
      this.isSubscribed = false;
      throw error;
    }
  }

  async close() {
    if (this.isSubscribed) {
      try {
        await this.subscriber.unsubscribe(DASHBOARD_EVENT_CHANNEL);
        await this.subscriber.quit();
        this.isSubscribed = false;
        logger.info('Unsubscribed from dashboard events');
      } catch (error) {
        logger.error('Error closing dashboard subscriber', { error: error.message });
      }
    }
  }

  /**
   * Handle metrics update event
   * @param {string} userId - The user ID
   */
  async handleMetricsUpdate(userId) {
    try {
      // Invalidate dashboard metrics cache for this user
      const cacheKey = `compass:notes:dashboard:metrics:${userId}`;
      await redisClient.del(cacheKey);
      logger.info('Invalidated dashboard metrics cache', { userId, cacheKey });
    } catch (error) {
      logger.error('Error handling metrics update event', { error: error.message });
    }
  }

  /**
   * Handle cache invalidate event
   * @param {string} userId - The user ID
   */
  async handleCacheInvalidate(userId) {
    try {
      // Invalidate all dashboard-related caches for this user
      const pattern = `compass:notes:dashboard:*:${userId}`;
      await redisClient.invalidateByPattern(pattern);
      logger.info('Invalidated all dashboard caches', { userId, pattern });
    } catch (error) {
      logger.error('Error handling cache invalidate event', { error: error.message });
    }
  }
}

module.exports = new DashboardEventSubscriber();