const NotePage = require('./model');
const { updateBidirectionalLinks, validateLinks } = require('./linkService');
const { ValidationError, NotFoundError, DatabaseError } = require('../../../pkg/utils/errorHandler');
const { logger } = require('../../../pkg/utils/logger');

class NoteService {
  /**
   * Create a new note page
   * @param {Object} input - Note data
   * @returns {Object} Created note
   */
  async createNote(input, selectedFields = '') {
    logger.debug('Creating note page', { input });
    
    if (!input.userId) {
      throw new ValidationError('User ID is required', 'userId');
    }

    if (!input.title?.trim()) {
      throw new ValidationError('Title is required', 'title');
    }

    // Validate links if provided
    if (input.linksOut && input.linksOut.length > 0) {
      try {
        await validateLinks(input.linksOut);
      } catch (error) {
        throw new ValidationError(error.message, 'linksOut');
      }
    }

    const note = new NotePage(input);
    await note.save();
    logger.info('Note page created', { noteId: note._id });

    const savedNote = await NotePage.findById(note._id)
      .select(`${selectedFields} userId tags`)
      .lean();
    if (!savedNote || !savedNote.userId) {
      throw new Error('Saved note is missing userId or does not exist');
    }

    // Cache the new note using unified API
    await global.redisClient.setEntity(
      'note',
      note._id.toString(),
      savedNote,
      [input.userId, ...(Array.isArray(input.tags) ? input.tags : [])],
      input.userId
    );

    // Invalidate user's note list cache
    await global.redisClient.invalidateByPattern(`user:${input.userId}:notes:*`);

    logger.info('Note page creation completed', { 
      noteId: note._id,
      userId: input.userId
    });

    return savedNote;
  }

  /**
   * Update an existing note page
   * @param {string} id - Note ID
   * @param {Object} input - Updated note data
   * @returns {Object} Updated note
   */
  async updateNote(id, input, selectedFields = '') {
    logger.debug('Updating note page', { noteId: id, input });

    if (!id) {
      throw new ValidationError('Note ID is required', 'id');
    }

    // Fetch the old note before updating
    const oldNote = await NotePage.findOne({ _id: id, isDeleted: false });
    if (!oldNote) {
      throw new NotFoundError('Note');
    }

    // Add validation for required fields if they're included in the update
    if (input.title !== undefined && !input.title?.trim()) {
      throw new ValidationError('Title is required', 'title');
    }

    // Validate links if provided
    if (input.linksOut?.length > 0) {
      await validateLinks(input.linksOut);
    }

    // Invalidate by tags for old note before update
    await global.redisClient.invalidateByTags([
      oldNote.userId.toString(),
      ...(Array.isArray(oldNote.tags) ? oldNote.tags : [])
    ]);
    // Invalidate old cache key and remove from tag sets
    await global.redisClient.invalidateByPattern(global.redisClient.generateKey('note', id));

    // Update note
    Object.assign(oldNote, input);
    await oldNote.save();
    logger.info('Note page updated', { noteId: id });

    const updatedNote = await NotePage.findById(id)
      .select(`${selectedFields} userId tags`)
      .lean();
    if (!updatedNote || !updatedNote.userId) {
      throw new Error('Updated note is missing userId or does not exist');
    }

    // Invalidate by tags for updated note after update
    await global.redisClient.invalidateByTags([
      updatedNote.userId.toString(),
      ...(Array.isArray(updatedNote.tags) ? updatedNote.tags : [])
    ]);
    // Cache the updated note
    await global.redisClient.setEntity(
      'note',
      id.toString(),
      updatedNote,
      [updatedNote.userId, ...(Array.isArray(updatedNote.tags) ? updatedNote.tags : [])],
      updatedNote.userId
    );
    
    // Invalidate user's note list cache
    await global.redisClient.invalidateByPattern(`user:${updatedNote.userId}:notes:*`);

    logger.info('Note page update completed', { 
      noteId: id,
      userId: oldNote.userId
    });

    return updatedNote;
  }

  /**
   * Delete (soft delete) a note page
   * @param {string} id - Note ID
   * @returns {Object} Deleted note
   */
  async deleteNote(id, selectedFields = '') {
    logger.debug('Deleting note page', { noteId: id });

    if (!id) {
      throw new ValidationError('Note ID is required', 'id');
    }

    // Fetch the old note before deleting
    const note = await NotePage.findOne({ _id: id, isDeleted: false });
    if (!note) {
      throw new NotFoundError('Note');
    }

    // Invalidate by tags for note before delete
    await global.redisClient.invalidateByTags([
      note.userId.toString(),
      ...(Array.isArray(note.tags) ? note.tags : [])
    ]);

    // Soft delete
    note.isDeleted = true;
    await note.save();
    logger.info('Note page marked as deleted', { noteId: id });

    const deletedNote = await NotePage.findById(id)
      .select(`${selectedFields} userId tags`)
      .lean();
    if (!deletedNote || !deletedNote.userId) {
      throw new Error('Deleted note is missing userId or does not exist');
    }

    // Invalidate user's note list cache
    await global.redisClient.invalidateByPattern(`user:${note.userId}:notes:*`);

    logger.info('Note page deletion completed', { 
      noteId: id,
      userId: note.userId
    });

    return deletedNote;
  }

  /**
   * Toggle favorite status of a note
   * @param {string} id - Note ID
   * @param {boolean} favorited - Favorite status
   * @returns {Object} Updated note
   */
  async toggleFavorite(id, favorited, selectedFields = '') {
    logger.debug('Toggling favorite status', { noteId: id, favorited });

    if (!id) {
      throw new ValidationError('Note ID is required', 'id');
    }

    if (typeof favorited !== 'boolean') {
      throw new ValidationError('Favorite status is required', 'favorited');
    }

    const note = await NotePage.findOne({ _id: id, isDeleted: false });
    if (!note) {
      throw new NotFoundError('Note');
    }

    note.favorited = favorited;
    await note.save();

    // Update cache
    try {
      await global.redisClient.setEntity(
        'note',
        id.toString(),
        note.toObject(),
        [note.userId, ...(Array.isArray(note.tags) ? note.tags : [])],
        note.userId
      );
      await global.redisClient.invalidateByPattern(`user:${note.userId}:notes:*`);
    } catch (cacheError) {
      logger.warn('Failed to update note cache', { 
        error: cacheError.message,
        noteId: id 
      });
    }

    logger.info('Note favorite status updated', { noteId: id, favorited });

    const updatedNote = await NotePage.findById(id)
      .select(`${selectedFields} userId tags`)
      .lean();
    if (!updatedNote || !updatedNote.userId) {
      throw new Error('Updated note is missing userId or does not exist');
    }

    return updatedNote;
  }

  /**
   * Get a note by ID (with cache)
   * @param {string} id - Note ID
   * @param {string} selectedFields - Fields to select
   * @returns {Object} Note
   */
  async getNote(id, selectedFields = '') {
    logger.debug('Getting note by ID', { noteId: id });
    if (!id) {
      throw new ValidationError('Note ID is required', 'id');
    }
    // Try to get from cache first
    const cachedNote = await global.redisClient.getEntity('note', id);
    if (cachedNote) {
      logger.debug('Note retrieved from cache', { noteId: id });
      return cachedNote;
    }
    const note = await NotePage.findOne({ _id: id, isDeleted: false })
      .select(selectedFields)
      .lean();
    if (!note) {
      throw new NotFoundError('Note');
    }
    // Cache the note
    await global.redisClient.setEntity(
      'note',
      id.toString(),
      note,
      [note.userId, ...(Array.isArray(note.tags) ? note.tags : [])],
      note.userId
    );
    logger.debug('Note cached', { noteId: id });
    return note;
  }

  /**
   * Get notes with pagination, filtering, and search (with cache)
   */
  async getNotes({ userId, search, page = 1, limit = 10, sortField = 'createdAt', sortOrder = -1, filter = {} }, selectedFields = '') {
    logger.debug('Getting notes', { userId, page, limit, sortField, sortOrder, filter, search });
    if (!userId) {
      throw new ValidationError('User ID is required', 'userId');
    }
    const cacheKey = global.redisClient.generateListKey(userId, 'notes', { page, limit, sortField, sortOrder, filter, search });
    const cachedResult = await global.redisClient.getList(cacheKey);
    if (cachedResult) {
      logger.debug('Notes retrieved from cache', { userId, page, limit });
      return cachedResult;
    }
    const skip = (page - 1) * limit;
    const query = { userId, isDeleted: false };
    // Apply filters if provided
    if (filter) {
      if (filter.tags && filter.tags.length > 0) {
        query.tags = { $in: filter.tags };
      }
      if (typeof filter.favorited === 'boolean') {
        query.favorited = filter.favorited;
      }
      if (filter.createdAfter || filter.createdBefore) {
        query.createdAt = {};
        if (filter.createdAfter) {
          query.createdAt.$gte = new Date(filter.createdAfter);
        }
        if (filter.createdBefore) {
          query.createdAt.$lte = new Date(filter.createdBefore);
        }
      }
    }
    const sortOptions = { [sortField]: sortOrder };
    let notes;
    let totalItems;
    if (search?.query) {
      logger.debug('Performing text search', { query: search.query });
      query.$text = {
        $search: search.query,
        $caseSensitive: false,
        $diacriticSensitive: false
      };
      notes = await NotePage.find(query)
        .select(selectedFields || 'title content tags favorited icon createdAt updatedAt userId')
        .sort({ score: { $meta: 'textScore' }, ...sortOptions })
        .skip(skip)
        .limit(limit)
        .lean();
    } else {
      notes = await NotePage.find(query)
        .select(selectedFields || 'title content tags favorited icon createdAt updatedAt userId')
        .sort(sortOptions)
        .skip(skip)
        .limit(limit)
        .lean();
    }
    totalItems = await NotePage.countDocuments(query);
    const result = {
      success: true,
      message: 'Notes retrieved successfully',
      data: notes,
      pageInfo: {
        totalItems,
        currentPage: page,
        totalPages: Math.ceil(totalItems / limit)
      }
    };
    // Collect all tags from the result set for robust invalidation
    const allTags = Array.from(new Set(notes.flatMap(n => n.tags || [])));
    await global.redisClient.setList(cacheKey, result, [userId, ...allTags], userId);
    logger.debug('Notes cached', { userId, page, limit, totalItems });
    logger.info('Notes retrieved successfully', { userId, page, limit, totalItems, hasSearch: !!search?.query });
    return result;
  }
}

module.exports = new NoteService(); 