const Journal = require('./model');
const { ValidationError, NotFoundError, DatabaseError } = require('../../../pkg/utils/errorHandler');
const { logger } = require('../../../pkg/utils/logger');

class JournalService {
  /**
   * Create a new journal entry
   * @param {Object} input - Journal data
   * @returns {Object} Created journal
   */
  async createJournal(input, selectedFields = '') {
    logger.debug('Creating journal entry', { input });
    
    if (!input.userId) {
      throw new ValidationError('User ID is required', 'userId');
    }

    if (!input.title?.trim()) {
      throw new ValidationError('Title is required', 'title');
    }

    if (!input.date) {
      throw new ValidationError('Date is required', 'date');
    }

    const journal = new Journal(input);
    await journal.save();
    logger.info('Journal entry created', { journalId: journal._id });

    const savedJournal = await Journal.findById(journal._id)
      .select(selectedFields)
      .lean();

    // Cache the new journal
    await global.redisClient.setJournal(
      journal._id,
      savedJournal
    );

    // Invalidate user's journal list cache
    await global.redisClient.clearByPattern(`user:${input.userId}:journals:*`);

    logger.info('Journal entry creation completed', { 
      journalId: journal._id,
      userId: input.userId
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

    const existingJournal = await Journal.findById(id);
    if (!existingJournal) {
      throw new NotFoundError('Journal');
    }

    // Add validation for required fields if they're included in the update
    if (input.title !== undefined && !input.title?.trim()) {
      throw new ValidationError('Title is required', 'title');
    }

    if (input.date !== undefined && !input.date) {
      throw new ValidationError('Date is required', 'date');
    }

    // Update journal
    Object.assign(existingJournal, input);
    await existingJournal.save();
    logger.info('Journal entry updated', { journalId: id });

    const updatedJournal = await Journal.findById(id)
      .select(selectedFields)
      .lean();

    // Update cache
    await global.redisClient.setJournal(id, updatedJournal);
    
    // Invalidate user's journal list cache
    await global.redisClient.clearByPattern(`user:${existingJournal.userId}:journals:*`);

    logger.info('Journal entry update completed', { 
      journalId: id,
      userId: existingJournal.userId
    });

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

    const journal = await Journal.findById(id);
    if (!journal) {
      throw new NotFoundError('Journal');
    }

    // Store journal data before deletion
    const deletedJournal = await Journal.findById(id)
      .select(selectedFields)
      .lean();

    // Delete the journal
    await Journal.deleteOne({ _id: id });
    logger.info('Journal entry deleted', { journalId: id });

    // Invalidate caches
    await Promise.all([
      global.redisClient.del(`journal:${id}`),
      global.redisClient.clearByPattern(`user:${journal.userId}:journals:*`)
    ]);

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
      .select(selectedFields)
      .lean();

    // Update the journal cache instead of invalidating it
    await global.redisClient.setJournal(id, archivedJournal);
    
    // Only invalidate the user's journal list caches
    await global.redisClient.clearByPattern(`user:${journal.userId}:journals:*`);

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

    const journals = await Journal.find({
      date: {
        $gte: startDate,
        $lte: endDate
      },
      userId,
      archived: false
    })
    .select(selectedFields)
    .lean();

    logger.info('Retrieved journals by date range', {
      userId,
      count: journals.length,
      startDate,
      endDate
    });

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
    const cachedJournal = await global.redisClient.getJournal(id);
    if (cachedJournal) {
      logger.debug('Journal retrieved from cache', { journalId: id });
      // If we don't want archived journals and this one is archived, return not found
      if (!includeArchived && cachedJournal.archived) {
        throw new NotFoundError('Journal');
      }
      return cachedJournal;
    }

    const query = { _id: id };
    // Only filter by archived status if we're not including archived journals
    if (!includeArchived) {
      query.archived = false;
    }

    const journal = await Journal.findOne(query)
      .select(selectedFields)
      .lean();
    
    if (!journal) {
      throw new NotFoundError('Journal');
    }

    // Cache the journal
    await global.redisClient.setJournal(id, journal);
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

    if (!userId) {
      throw new ValidationError('User ID is required', 'userId');
    }

    // Validate sortField to prevent MongoDB injection or errors
    const validSortFields = ['date', 'createdAt', 'updatedAt', 'title', 'wordCount', 'mood'];
    if (!validSortFields.includes(sortField)) {
      throw new ValidationError(`Invalid sort field: ${sortField}. Valid options are: ${validSortFields.join(', ')}`, 'sortField');
    }

    // Generate cache key based on query parameters
    const cacheKey = `user:${userId}:journals:${page}:${limit}:${sortField}:${sortOrder}:${JSON.stringify(filter)}`;

    // Try to get from cache first
    const cachedResult = await global.redisClient.get(cacheKey);
    if (cachedResult) {
      logger.debug('Journals retrieved from cache', { userId, page, limit });
      return cachedResult;
    }

    const skip = (page - 1) * limit;
    const query = { userId };
    
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
    await global.redisClient.set(cacheKey, result);
    logger.debug('Journals cached', { userId, page, limit, totalItems });

    logger.info('Journals retrieved successfully', { userId, page, limit, totalItems });
    return result;
  }
}

module.exports = new JournalService(); 