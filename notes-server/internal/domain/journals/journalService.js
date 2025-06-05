const Journal = require('./model');
const { ValidationError, NotFoundError, DatabaseError } = require('../../../pkg/utils/errorHandler');
const { logger } = require('../../../pkg/utils/logger');
const RedisService = require('../../infrastructure/cache/redisService');
const redisConfig = require('../../infrastructure/cache/config');

const redisClient = new RedisService(redisConfig);

class JournalService {
  /**
   * Create a new journal entry
   * @param {Object} input - Journal data
   * @returns {Object} Created journal
   */
  async createJournal(input, selectedFields = '') {
    logger.debug('Creating journal entry', { input });
    // Always set userId from input.userId (which is set by resolver from context)
    const userId = input.userId;
    if (!userId) {
      throw new ValidationError('User ID is required', 'userId');
    }
    if (!input.title?.trim()) {
      throw new ValidationError('Title is required', 'title');
    }
    if (!input.date) {
      throw new ValidationError('Date is required', 'date');
    }
    const journal = new Journal({ ...input, userId });
    await journal.save();
    logger.info('Journal entry created', { journalId: journal._id });
    const savedJournal = await Journal.findById(journal._id)
      .select(`${selectedFields} userId tags`)
      .lean();
    if (!savedJournal || !savedJournal.userId) {
      throw new Error('Saved journal is missing userId or does not exist');
    }

    // Cache the new journal using unified API
    await redisClient.setEntity(
      'journal',
      journal._id.toString(),
      savedJournal,
      [userId, ...(Array.isArray(input.tags) ? input.tags : [])],
      userId
    );

    // Invalidate user's journal list cache
    await redisClient.invalidateByPattern(`user:${userId}:journals:*`);

    logger.info('Journal entry creation completed', { 
      journalId: journal._id,
      userId: userId
    });

    return savedJournal;
  }

  /**
   * Update an existing journal entry
   * @param {string} id - Journal ID
   * @param {Object} input - Updated journal data
   * @returns {Object} Updated journal
   */
  async updateJournal(id, input, selectedFields = '') {
    logger.debug('Updating journal entry', { journalId: id, input });
    if (!id) {
      throw new ValidationError('Journal ID is required', 'id');
    }
    // Fetch the old journal before updating
    const oldJournal = await Journal.findById(id);
    if (!oldJournal) {
      throw new NotFoundError('Journal');
    }
    await redisClient.invalidateByTags([
      oldJournal.userId.toString(),
      ...(Array.isArray(oldJournal.tags) ? oldJournal.tags : [])
    ]);
    await redisClient.invalidateByPattern(redisClient.generateKey('journal', id));
    if (input.title !== undefined && !input.title?.trim()) {
      throw new ValidationError('Title is required', 'title');
    }
    if (input.date !== undefined && !input.date) {
      throw new ValidationError('Date is required', 'date');
    }
    // Always set userId from input.userId (which is set by resolver from context)
    Object.assign(oldJournal, { ...input, userId: input.userId });
    await oldJournal.save();
    logger.info('Journal entry updated', { journalId: id });
    const updatedJournal = await Journal.findById(id)
      .select(`${selectedFields} userId tags`)
      .lean();
    if (!updatedJournal || !updatedJournal.userId) {
      throw new Error('Updated journal is missing userId or does not exist');
    }
    await redisClient.invalidateByTags([
      updatedJournal.userId.toString(),
      ...(Array.isArray(updatedJournal.tags) ? updatedJournal.tags : [])
    ]);
    await redisClient.setEntity(
      'journal',
      id.toString(),
      updatedJournal,
      [updatedJournal.userId, ...(Array.isArray(updatedJournal.tags) ? updatedJournal.tags : [])],
      updatedJournal.userId
    );
    await redisClient.invalidateByPattern(`user:${updatedJournal.userId}:journals:*`);
    logger.info('Journal entry update completed', { journalId: id, userId: updatedJournal.userId });
    return updatedJournal;
  }
  
  /**
   * Permanently delete a journal entry
   * @param {string} id - Journal ID
   * @returns {Object} Deleted journal
   */
  async deleteJournal(id, selectedFields = '') {
    logger.debug('Deleting journal entry', { journalId: id });

    if (!id) {
      throw new ValidationError('Journal ID is required', 'id');
    }

    // Fetch the old journal before deleting
    const journal = await Journal.findOne({ _id: id, isDeleted: false });
    if (!journal) {
      throw new NotFoundError('Journal');
    }

    // Soft delete
    journal.isDeleted = true;
    await journal.save();

    // Invalidate by tags for journal before delete
    await redisClient.invalidateByTags([
      journal.userId.toString(),
      ...(Array.isArray(journal.tags) ? journal.tags : [])
    ]);
    await redisClient.invalidateByPattern(redisClient.generateKey('journal', id));

    const deletedJournal = await Journal.findById(id)
      .select(`${selectedFields} userId tags`)
      .lean();
    if (!deletedJournal || !deletedJournal.userId) {
      throw new Error('Deleted journal is missing userId or does not exist');
    }

    // Invalidate user's journal list cache
    await redisClient.invalidateByPattern(`user:${journal.userId}:journals:*`);

    logger.info('Journal entry deletion completed', { 
      journalId: id,
      userId: journal.userId
    });

    return deletedJournal;
  }

  /**
   * Archive a journal entry
   * @param {string} id - Journal ID
   * @returns {Object} Archived journal
   */
  async archiveJournal(id, selectedFields = '') {
    logger.debug('Archiving journal entry', { journalId: id });

    if (!id) {
      throw new ValidationError('Journal ID is required', 'id');
    }

    const journal = await Journal.findById(id);
    if (!journal) {
      throw new NotFoundError('Journal');
    }

    journal.archived = true;
    await journal.save();
    logger.info('Journal entry archived', { journalId: id });

    const archivedJournal = await Journal.findById(id)
      .select(`${selectedFields} userId tags`)
      .lean();
    if (!archivedJournal || !archivedJournal.userId) {
      throw new Error('Archived journal is missing userId or does not exist');
    }

    // Update the journal cache instead of invalidating it
    await redisClient.setEntity(
      'journal',
      id.toString(),
      archivedJournal,
      [journal.userId.toString(), ...(Array.isArray(journal.tags) ? journal.tags : [])],
      journal.userId
    );
    
    // Only invalidate the user's journal list caches
    await redisClient.invalidateByPattern(`user:${journal.userId}:journals:*`);

    logger.info('Journal entry archival completed', { 
      journalId: id,
      userId: journal.userId
    });

    return archivedJournal;
  }

  /**
   * Get journal entries by date range
   * @param {Date} startDate - Start date
   * @param {Date} endDate - End date
   * @param {string} userId - User ID
   * @returns {Array} Journal entries
   */
  async getJournalsByDateRange(startDate, endDate, userId, selectedFields = '') {
    logger.debug('Getting journals by date range', { startDate, endDate, userId });
    // Always require userId from argument, never from input
    if (!userId) {
      throw new ValidationError('User ID is required', 'userId');
    }

    const cacheKey = redisClient.generateListKey(userId, 'journals:dateRange', { startDate, endDate, selectedFields });
    const cachedResult = await redisClient.getList(cacheKey);
    if (cachedResult) {
      logger.debug('Journals by date range retrieved from cache', { userId, startDate, endDate });
      return cachedResult;
    }

    const journals = await Journal.find({
      date: {
        $gte: startDate,
        $lte: endDate
      },
      userId,
      archived: false,
      isDeleted: false
    })
    .select(selectedFields)
    .lean();

    logger.info('Retrieved journals by date range', {
      userId,
      count: journals.length,
      startDate,
      endDate
    });

    // Cache the result
    const allTags = Array.from(new Set(journals.flatMap(j => j.tags || [])));
    await redisClient.setList(cacheKey, journals, [userId, ...allTags], userId);

    return journals;
  }

  /**
   * Get a single journal by ID
   * @param {string} id - Journal ID
   * @param {string} selectedFields - Fields to select
   * @param {boolean} includeArchived - Whether to include archived journals
   * @returns {Object} Journal entry
   */
  async getJournal(id, selectedFields = '', includeArchived = false) {
    logger.debug('Getting journal by ID', { journalId: id, includeArchived });

    if (!id) {
      throw new ValidationError('Journal ID is required', 'id');
    }

    // Try to get from cache first
    const cachedJournal = await redisClient.getEntity('journal', id);
    if (cachedJournal) {
      logger.debug('Journal retrieved from cache', { journalId: id });
      // If we don't want archived journals and this one is archived, return not found
      if (!includeArchived && cachedJournal.archived) {
        throw new NotFoundError('Journal');
      }
      if (cachedJournal.isDeleted) {
        throw new NotFoundError('Journal');
      }
      return cachedJournal;
    }

    const query = { _id: id, isDeleted: false };
    // Only filter by archived status if we're not including archived journals
    if (!includeArchived) {
      query.archived = false;
    }

    const journal = await Journal.findOne(query)
      .select(`${selectedFields} userId tags`)
      .lean();
    
    if (!journal || !journal.userId) {
      throw new NotFoundError('Journal');
    }

    // Cache the result
    const tags = [journal.userId.toString(), ...(Array.isArray(journal.tags) ? journal.tags : [])];
    await redisClient.setEntity(
      'journal',
      id.toString(),
      journal,
      tags,
      journal.userId
    );
    logger.debug('Journal cached', { journalId: id });

    logger.info('Journal retrieved successfully', { journalId: id });
    return journal;
  }

  /**
   * Get journals with pagination and filtering
   * @param {Object} params - Query parameters
   * @param {string} selectedFields - Fields to select
   * @returns {Object} Paginated journals response
   */
  async getJournals({ userId, page = 1, limit = 10, sortField = 'date', sortOrder = -1, filter = {} }, selectedFields = '') {
    logger.debug('Getting journals', { userId, page, limit, sortField, sortOrder, filter });
    // Always require userId from argument, never from input
    if (!userId) {
      throw new ValidationError('User ID is required', 'userId');
    }

    // Validate sortField to prevent MongoDB injection or errors
    const validSortFields = ['date', 'createdAt', 'updatedAt', 'title', 'wordCount', 'mood'];
    if (!validSortFields.includes(sortField)) {
      throw new ValidationError(`Invalid sort field: ${sortField}. Valid options are: ${validSortFields.join(', ')}`, 'sortField');
    }

    // Generate cache key based on query parameters
    const cacheKey = redisClient.generateListKey(userId, 'journals', { page, limit, sortField, sortOrder, filter });

    // Try to get from cache first
    const cachedResult = await redisClient.getList(cacheKey);
    if (cachedResult) {
      logger.debug('Journals retrieved from cache', { userId, page, limit });
      return cachedResult;
    }

    const skip = (page - 1) * limit;
    const query = { userId, isDeleted: false };
    
    // Only apply archived: false if filter.archived is not explicitly set
    if (filter.archived !== undefined) {
      query.archived = filter.archived;
    } else {
      query.archived = false; // Default behavior
    }

    // Apply filters
    if (filter.tags?.length > 0) {
      query.tags = { $in: filter.tags };
    }
    if (filter.mood) {
      query.mood = filter.mood;
    }
    if (filter.dateFrom || filter.dateTo) {
      query.date = {};
      if (filter.dateFrom) {
        query.date.$gte = new Date(filter.dateFrom);
      }
      if (filter.dateTo) {
        query.date.$lte = new Date(filter.dateTo);
      }
    }

    const [journals, totalItems] = await Promise.all([
      Journal.find(query)
        .select(selectedFields || 'title content tags mood date wordCount createdAt updatedAt userId')
        .sort({ [sortField]: sortOrder })
        .skip(skip)
        .limit(limit)
        .lean(),
      Journal.countDocuments(query)
    ]);

    const result = {
      success: true,
      message: 'Journals retrieved successfully',
      data: journals,
      pageInfo: {
        totalItems,
        currentPage: page,
        totalPages: Math.ceil(totalItems / limit)
      }
    };

    // Cache the result
    // Collect all tags from the result set for robust invalidation
    const allTags = Array.from(new Set(journals.flatMap(j => j.tags || [])));
    await redisClient.setList(cacheKey, result, [userId, ...allTags], userId);
    logger.debug('Journals cached', { userId, page, limit, totalItems });

    logger.info('Journals retrieved successfully', { userId, page, limit, totalItems });
    return result;
  }
}

module.exports = new JournalService(); 