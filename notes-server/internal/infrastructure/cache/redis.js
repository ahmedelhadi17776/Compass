const Redis = require('ioredis');
const { promisify } = require('util');
const { gzip, gunzip } = require('zlib');
const NotePage = require('../../domain/notes/model');

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

    this.client = new Redis({
      host: this.config.host,
      port: this.config.port,
      password: this.config.password,
      db: this.config.db,
      retryStrategy: (times) => {
        if (times > this.config.maxRetries) return null;
        return this.config.retryDelay * Math.pow(2, times);
      }
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
        console.error('Redis health check failed:', error);
      }
    }, 10000); // Check every 10 seconds
  }

  isHealthy() {
    return this.health;
  }

  async compress(data) {
    if (!this.config.useCompression) return data;
    try {
      const buffer = await gzipAsync(JSON.stringify(data));
      return buffer.toString('base64');
    } catch (error) {
      console.error('Compression failed:', error);
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
      console.error('Decompression failed:', error);
      return data;
    }
  }

  generateKey(entityType, entityId, action = '') {
    return `${this.config.keyPrefix}${entityType}:${entityId}${action ? ':' + action : ''}`;
  }

  async get(key) {
    try {
      const data = await this.client.get(key);
      if (!data) {
        this.trackCacheEvent(false, 'get');
        return null;
      }
      this.trackCacheEvent(true, 'get');
      // Parse the JSON string back to an object
      return JSON.parse(data);
    } catch (error) {
      console.error('Redis get error:', error);
      return null;
    }
  }

  async set(key, value, ttl = this.config.defaultTTL) {
    try {
      // Always stringify the value before storing
      const stringValue = JSON.stringify(value);
      await this.client.set(key, stringValue, 'EX', ttl);
      return true;
    } catch (error) {
      console.error('Redis set error:', error);
      return false;
    }
  }

  async delete(key) {
    try {
      await this.client.del(key);
      return true;
    } catch (error) {
      console.error('Redis delete error:', error);
      return false;
    }
  }

  async clearByPattern(pattern) {
    try {
      const keys = await this.client.keys(`${this.config.keyPrefix}${pattern}`);
      if (keys.length > 0) {
        await this.client.del(keys);
      }
      return true;
    } catch (error) {
      console.error('Redis clear pattern error:', error);
      return false;
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

    return {
      hits: this.metrics.hits,
      misses: this.metrics.misses,
      hitRate: hitRate.toFixed(2) + '%',
      byType: Object.fromEntries(this.metrics.byType),
      health: this.isHealthy()
    };
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
        ...uniqueKeys.map(key => this.delete(key)),
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
    const key = this.generateKey('note', noteId);
    return this.cacheWithTags(
      key,
      data,
      [data.userId.toString(), ...data.tags]
    );
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

  // Close the Redis connection
  async close() {
    await this.client.quit();
  }
}

module.exports = RedisClient;