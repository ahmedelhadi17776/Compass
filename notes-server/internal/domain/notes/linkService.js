const NotePage = require('./model');
const { DatabaseError } = require('../../../pkg/utils/errorHandler');
const { updateBidirectionalLinks, handleCascadingDelete } = require('../../api/middleware/noteHooks');

// Helper function to validate links
async function validateLinks(linksOut) {
  try {
    if (!Array.isArray(linksOut)) {
      throw new DatabaseError('linksOut must be an array');
    }

    if (linksOut.length === 0) {
      return true;
    }

    // Convert all IDs to strings for comparison
    const linkIds = linksOut.map(id => id.toString());

    // Check for duplicate links
    const uniqueLinks = new Set(linkIds);
    if (uniqueLinks.size !== linkIds.length) {
      throw new DatabaseError('Duplicate links are not allowed');
    }

    // Find all notes that exist and are not deleted
    const existingNotes = await NotePage.find({
      _id: { $in: linksOut },
      isDeleted: false
    }).select('_id');

    const existingIds = existingNotes.map(note => note._id.toString());
    const invalidLinks = linkIds.filter(id => !existingIds.includes(id));

    if (invalidLinks.length > 0) {
      throw new DatabaseError(`Invalid or deleted notes found: ${invalidLinks.join(', ')}`);
    }

    return true;
  } catch (error) {
    if (error instanceof DatabaseError) {
      throw error;
    }
    throw new DatabaseError(`Failed to validate links: ${error.message}`);
  }
}

// Helper function to get linked notes
async function getLinkedNotes(noteId) {
  try {
    const note = await NotePage.findById(noteId)
      .populate('linksOut', 'title content tags favorited icon')
      .populate('linksIn', 'title content tags favorited icon');

    if (!note) {
      throw new DatabaseError('Note not found');
    }

    return {
      linksOut: note.linksOut,
      linksIn: note.linksIn
    };
  } catch (error) {
    if (error instanceof DatabaseError) {
      throw error;
    }
    throw new DatabaseError(`Failed to get linked notes: ${error.message}`);
  }
}

// Helper function to get note link statistics
async function getNoteLinkStats(noteId) {
  try {
    const note = await NotePage.findById(noteId);
    if (!note) {
      throw new DatabaseError('Note not found');
    }

    return {
      totalLinks: note.linksOut.length + note.linksIn.length,
      outgoingLinks: note.linksOut.length,
      incomingLinks: note.linksIn.length
    };
  } catch (error) {
    if (error instanceof DatabaseError) {
      throw error;
    }
    throw new DatabaseError(`Failed to get note link stats: ${error.message}`);
  }
}

module.exports = { 
  updateBidirectionalLinks,
  handleCascadingDelete,
  validateLinks,
  getLinkedNotes,
  getNoteLinkStats
};