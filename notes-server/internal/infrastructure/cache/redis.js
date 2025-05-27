const Redis = require('ioredis');
const { promisify } = require('util');
const { gzip, gunzip } = require('zlib');
const NotePage = require('../../domain/notes/model');
const { logger } = require('../../../pkg/utils/logger');
const { DatabaseError } = require('../../../pkg/utils/errorHandler');
const Journal = require('../../domain/journals/model');

const gzipAsync = promisify(gzip);
const gunzipAsync = promisify(gunzip);

class RedisClient {
  constructor(config) {
    this.config = {
      host: config.host || 'localhost',
      port: config.port || 6380,
      password: config.password || '',
      db: config.db || 2,
      keyPrefix: 'compass:notes:',
      maxRetries: 3,
      retryDelay: 100,
      useCompression: false,
      defaultTTL: 30 * 60, 
      ...config
    };

    logger.info('Initializing Redis client', { 
      host: this.config.host,
      port: this.config.port,
      db: this.config.db
    });

    this.client = new Redis({
      host: this.config.host,
      port: this.config.port,
      password: this.config.password,
      db: this.config.db,
      retryStrategy: (times) => {
        const delay = Math.min(times * 50, 2000);
        logger.info('Redis reconnecting...', { attempt: times, delay });
        return delay;
      },
      maxRetriesPerRequest: 3
    });

    this.client.on('error', (error) => {
      logger.error('Redis client error:', { error: error.message });
    });

    this.client.on('connect', () => {
      logger.info('Redis client connected');
    });

    this.client.on('ready', () => {
      logger.info('Redis client ready');
    });

    this.client.on('reconnecting', () => {
      logger.info('Redis client reconnecting');
    });

    this.client.on('end', () => {
      logger.info('Redis client connection ended');
    });

    this.metrics = {
      hits: 0,
      misses: 0,
      byType: new Map()
    };

    // Initialize health check
    this.health = true;
    this.startHealthCheck();
  }

  async startHealthCheck() {
    setInterval(async () => {
      try {
        await this.client.ping();
        this.health = true;
      } catch (error) {
        this.health = false;
        logger.error('Redis health check failed:', { error: error.message });
      }
    }, 10000); // Check every 10 seconds
  }

  async isHealthy() {
    try {
      if (!this.client.status === 'ready') {
        return false;
      }
      await this.client.ping();
      return true;
    } catch (error) {
      logger.error('Redis health check failed:', { error: error.message });
      return false;
    }
  }

  async compress(data) {
    if (!this.config.useCompression) return data;
    try {
      const buffer = await gzipAsync(JSON.stringify(data));
      return buffer.toString('base64');
    } catch (error) {
      logger.error('Compression failed:', { error: error.message });
      return data;
    }
  }

  async decompress(data) {
    if (!this.config.useCompression) return data;
    try {
      const buffer = Buffer.from(data, 'base64');
      const decompressed = await gunzipAsync(buffer);
      return JSON.parse(decompressed.toString());
    } catch (error) {
      logger.error('Decompression failed:', { error: error.message });
      return data;
    }
  }

  generateKey(entityType, entityId, action = '') {
    return `${this.config.keyPrefix}${entityType}:${entityId}${action ? ':' + action : ''}`;
  }

  async get(key) {
    try {
      const value = await this.client.get(key);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      logger.error('Redis get error:', { key, error: error.message });
      throw new DatabaseError(`Failed to get value from Redis: ${error.message}`);
    }
  }

  async set(key, value, ttl = null) {
    try {
      const stringValue = JSON.stringify(value);
      if (ttl) {
        await this.client.setex(key, ttl, stringValue);
      } else {
        await this.client.set(key, stringValue);
      }
    } catch (error) {
      logger.error('Redis set error:', { key, error: error.message });
      throw new DatabaseError(`Failed to set value in Redis: ${error.message}`);
    }
  }

  async del(key) {
    try {
      await this.client.del(key);
    } catch (error) {
      logger.error('Redis delete error:', { key, error: error.message });
      throw new DatabaseError(`Failed to delete value from Redis: ${error.message}`);
    }
  }

  async clearByPattern(pattern) {
    try {
      const keys = await this.client.keys(pattern);
      if (keys.length > 0) {
        await this.client.del(keys);
      }
    } catch (error) {
      logger.error('Redis clear pattern error:', { pattern, error: error.message });
      throw new DatabaseError(`Failed to clear pattern from Redis: ${error.message}`);
    }
  }

  trackCacheEvent(hit, type) {
    if (hit) {
      this.metrics.hits++;
    } else {
      this.metrics.misses++;
    }

    const typeMetrics = this.metrics.byType.get(type) || { hits: 0, misses: 0 };
    if (hit) {
      typeMetrics.hits++;
    } else {
      typeMetrics.misses++;
    }
    this.metrics.byType.set(type, typeMetrics);
  }

  getMetrics() {
    const total = this.metrics.hits + this.metrics.misses;
    const hitRate = total > 0 ? (this.metrics.hits / total) * 100 : 0;

    const metrics = {
      hits: this.metrics.hits,
      misses: this.metrics.misses,
      hitRate: hitRate.toFixed(2) + '%',
      byType: Object.fromEntries(this.metrics.byType),
      health: this.isHealthy()
    };

    logger.debug('Cache metrics', { metrics });
    return metrics;
  }

  async cacheResponse(key, ttl, type, fn) {
    // Try to get from cache first
    const cached = await this.get(key);
    if (cached) {
      return cached;
    }

    // Cache miss, execute the function
    const result = await fn();
    if (result) {
      await this.set(key, result, ttl);
    }
    return result;
  }

  async invalidateCache(entityType, entityId) {
    const pattern = `${entityType}:${entityId}*`;
    return this.clearByPattern(pattern);
  }

  // Enhanced cache invalidation patterns
  async invalidateUserCache(userId) {
    const patterns = [
      `user:${userId}:notes:*`,
      `user:${userId}:flashcards:*`,
      `user:${userId}:journal:*`,
      `user:${userId}:canvas:*`
    ];
    
    await Promise.all(patterns.map(pattern => this.clearByPattern(pattern)));
  }

  async invalidateNoteCache(noteId, userId) {
    const patterns = [
      `note:${noteId}`,
      `user:${userId}:notes:*`
    ];
    
    await Promise.all(patterns.map(pattern => this.clearByPattern(pattern)));
  }

  async invalidateLinkedNotesCache(noteId, linkedNoteIds) {
    const patterns = linkedNoteIds.map(id => `note:${id}`);
    await Promise.all(patterns.map(pattern => this.clearByPattern(pattern)));
  }

  async invalidateSearchCache(userId, query) {
    const pattern = `user:${userId}:notes:*${query}*`;
    await this.clearByPattern(pattern);
  }

  async invalidateTagCache(userId, tag) {
    const pattern = `user:${userId}:notes:*${tag}*`;
    await this.clearByPattern(pattern);
  }

  // Enhanced caching strategies
  async cacheWithTags(key, value, tags, ttl = this.config.defaultTTL) {
    try {
      // Store the value
      await this.set(key, value, ttl);
      
      // Store the key in each tag's set
      const tagSets = tags.map(tag => `${this.config.keyPrefix}tag:${tag}`);
      await Promise.all(tagSets.map(tagSet => 
        this.client.sadd(tagSet, key)
      ));
      
      return true;
    } catch (error) {
      console.error('Cache with tags error:', error);
      return false;
    }
  }

  async invalidateByTags(tags) {
    try {
      // Get all keys associated with the tags
      const tagSets = tags.map(tag => `${this.config.keyPrefix}tag:${tag}`);
      const keys = await Promise.all(tagSets.map(tagSet => 
        this.client.smembers(tagSet)
      ));
      
      // Flatten and deduplicate keys
      const uniqueKeys = [...new Set(keys.flat())];
      
      // Delete all keys and their tag associations
      await Promise.all([
        ...uniqueKeys.map(key => this.del(key)),
        ...tagSets.map(tagSet => this.client.del(tagSet))
      ]);
      
      return true;
    } catch (error) {
      console.error('Invalidate by tags error:', error);
      return false;
    }
  }

  // Enhanced note-specific methods
  async getNotePage(noteId) {
    return this.cacheResponse(
      this.generateKey('note', noteId),
      this.config.defaultTTL,
      'note',
      async () => {
        const note = await NotePage.findById(noteId).lean();
        if (note) {
          // Cache with tags for better invalidation
          await this.cacheWithTags(
            this.generateKey('note', noteId),
            note,
            [note.userId.toString(), ...note.tags]
          );
        }
        return note;
      }
    );
  }

  async setNotePage(noteId, data) {
    try {
      if (!noteId || !data) {
        logger.warn('Invalid note data for caching', { noteId, hasData: !!data });
        return false;
      }

      const key = this.generateKey('note', noteId);
      const tags = [
        data.userId?.toString() || 'unknown',
        ...(Array.isArray(data.tags) ? data.tags : [])
      ];

      return this.cacheWithTags(key, data, tags);
    } catch (error) {
      logger.error('Error caching note page', { 
        error: error.message,
        noteId,
        hasData: !!data
      });
      return false;
    }
  }

  async getNotePagesByUser(userId, page = 1, limit = 10, filters = {}) {
    const key = this.generateKey('user', userId, `notes:${page}:${limit}:${JSON.stringify(filters)}`);
    return this.cacheResponse(
      key,
      this.config.defaultTTL,
      'user_notes',
      async () => {
        const notes = await NotePage.find({
          userId,
          isDeleted: false,
          ...filters
        })
        .sort({ createdAt: -1 })
        .skip((page - 1) * limit)
        .limit(limit)
        .lean();

        // Cache individual notes
        await Promise.all(notes.map(note => 
          this.setNotePage(note._id.toString(), note)
        ));

        return notes;
      }
    );
  }

  // Note-specific cache methods
  async getNotePagesByUser(userId, page = 1, limit = 10) {
    return this.get(this.generateKey('user', userId, `notes:${page}:${limit}`));
  }

  async setNotePagesByUser(userId, data, page = 1, limit = 10) {
    return this.set(this.generateKey('user', userId, `notes:${page}:${limit}`), data);
  }

  async getTemplate(templateId) {
    return this.get(this.generateKey('template', templateId));
  }

  async setTemplate(templateId, data) {
    return this.set(this.generateKey('template', templateId), data);
  }

  async getAINoteSnapshot(snapshotId) {
    return this.get(this.generateKey('ai_note', snapshotId));
  }

  async setAINoteSnapshot(snapshotId, data) {
    return this.set(this.generateKey('ai_note', snapshotId), data);
  }

  async getFlashcards(userId, page = 1, limit = 10) {
    return this.get(this.generateKey('user', userId, `flashcards:${page}:${limit}`));
  }

  async setFlashcards(userId, data, page = 1, limit = 10) {
    return this.set(this.generateKey('user', userId, `flashcards:${page}:${limit}`), data);
  }

  async getJournalEntry(userId, date) {
    return this.get(this.generateKey('user', userId, `journal:${date}`));
  }

  async setJournalEntry(userId, date, data) {
    return this.set(this.generateKey('user', userId, `journal:${date}`), data);
  }

  async getCanvasNode(canvasId, nodeId) {
    return this.get(this.generateKey('canvas', canvasId, `node:${nodeId}`));
  }

  async setCanvasNode(canvasId, nodeId, data) {
    return this.set(this.generateKey('canvas', canvasId, `node:${nodeId}`), data);
  }

  async getJournal(journalId) {
    return this.cacheResponse(
      this.generateKey('journal', journalId),
      this.config.defaultTTL,
      'journal',
      async () => {
        const journal = await Journal.findById(journalId).lean();
        if (journal) {
          // Cache with tags for better invalidation
          await this.cacheWithTags(
            this.generateKey('journal', journalId),
            journal,
            [journal.userId.toString(), ...(journal.tags || [])]
          );
        }
        return journal;
      }
    );
  }

  async setJournal(journalId, data) {
    try {
      if (!journalId || !data) {
        logger.warn('Invalid journal data for caching', { journalId, hasData: !!data });
        return false;
      }

      const key = this.generateKey('journal', journalId);
      const tags = [
        data.userId?.toString() || 'unknown',
        ...(Array.isArray(data.tags) ? data.tags : [])
      ];

      return this.cacheWithTags(key, data, tags);
    } catch (error) {
      logger.error('Error caching journal', { 
        error: error.message,
        journalId,
        hasData: !!data
      });
      return false;
    }
  }

  // Close the Redis connection
  async close() {
    try {
      await this.client.quit();
      logger.info('Redis connection closed');
    } catch (error) {
      logger.error('Error closing Redis connection:', { error: error.message });
      throw new DatabaseError(`Failed to close Redis connection: ${error.message}`);
    }
  }
}

module.exports = RedisClient;