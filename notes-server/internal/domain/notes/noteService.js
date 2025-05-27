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

    // Update bidirectional links if any
    if (input.linksOut?.length > 0) {
      await updateBidirectionalLinks(note._id, [], input.linksOut);
      logger.debug('Bidirectional links updated', { 
        noteId: note._id,
        linksOut: input.linksOut
      });
    }

    const savedNote = await NotePage.findById(note._id)
      .select(selectedFields)
      .lean();

    // Cache the new note
    await global.redisClient.setNotePage(
      note._id.toString(), 
      savedNote
    );

    // Invalidate user's note list cache
    await global.redisClient.clearByPattern(`user:${input.userId}:notes:*`);

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

    const existingNote = await NotePage.findById(id);
    if (!existingNote) {
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

    // Update note
    Object.assign(existingNote, input);
    await existingNote.save();
    logger.info('Note page updated', { noteId: id });

    // Update bidirectional links if changed
    if (input.linksOut) {
      await updateBidirectionalLinks(id, existingNote.linksOut, input.linksOut);
      logger.debug('Bidirectional links updated', { 
        noteId: id,
        oldLinks: existingNote.linksOut,
        newLinks: input.linksOut
      });
    }

    const updatedNote = await NotePage.findById(id)
      .select(selectedFields)
      .lean();

    // Update cache
    await global.redisClient.setNotePage(
      id.toString(),
      updatedNote
    );
    
    // Invalidate related caches
    await Promise.all([
      global.redisClient.clearByPattern(`user:${existingNote.userId}:notes:*`),
      ...existingNote.linksOut.map(linkedId => 
        global.redisClient.invalidateCache('note', linkedId)
      ),
      ...existingNote.linksIn.map(linkedId => 
        global.redisClient.invalidateCache('note', linkedId)
      )
    ]);

    logger.info('Note page update completed', { 
      noteId: id,
      userId: existingNote.userId
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

    const note = await NotePage.findById(id);
    if (!note) {
      throw new NotFoundError('Note');
    }

    // Soft delete
    note.isDeleted = true;
    await note.save();
    logger.info('Note page marked as deleted', { noteId: id });

    // Remove bidirectional links
    if (note.linksOut?.length > 0) {
      await updateBidirectionalLinks(id, note.linksOut, []);
      logger.debug('Bidirectional links removed', { 
        noteId: id,
        linksOut: note.linksOut
      });
    }

    const deletedNote = await NotePage.findById(id)
      .select(selectedFields)
      .lean();

    // Invalidate all related caches
    await Promise.all([
      global.redisClient.invalidateCache('note', id),
      global.redisClient.clearByPattern(`user:${note.userId}:notes:*`),
      ...note.linksOut.map(linkedId => 
        global.redisClient.invalidateCache('note', linkedId)
      ),
      ...note.linksIn.map(linkedId => 
        global.redisClient.invalidateCache('note', linkedId)
      )
    ]);

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

    const note = await NotePage.findById(id);
    if (!note) {
      throw new NotFoundError('Note');
    }

    note.favorited = favorited;
    await note.save();

    // Update cache
    if (global.redisClient) {
        try {
          await global.redisClient.setNotePage(id, note.toObject());
          await global.redisClient.clearByPattern(`user:${note.userId}:notes:*`);
        } catch (cacheError) {
          logger.warn('Failed to update note cache', { 
            error: cacheError.message,
            noteId: id 
          });
        }
    }

    logger.info('Note favorite status updated', { noteId: id, favorited });

    const updatedNote = await NotePage.findById(id)
      .select(selectedFields)
      .lean();

    return updatedNote;
  }
}

module.exports = new NoteService(); 