const NotePage = require('./model');
const { DatabaseError } = require('../../../pkg/utils/errorHandler');

async function updateBidirectionalLinks(noteId, newLinksOut, oldLinksOut = []) {
  try {
    // Use bulk operations for better performance
    const bulkOps = [];
    
    // Remove old links
    const removedLinks = oldLinksOut.filter(link => !newLinksOut.includes(link.toString()));
    if (removedLinks.length > 0) {
      bulkOps.push({
        updateMany: {
          filter: { _id: { $in: removedLinks } },
          update: { $pull: { linksIn: noteId } }
        }
      });
    }
    
    // Add new links
    const newLinks = newLinksOut.filter(link => !oldLinksOut.map(l => l.toString()).includes(link.toString()));
    if (newLinks.length > 0) {
      bulkOps.push({
        updateMany: {
          filter: { _id: { $in: newLinks } },
          update: { $addToSet: { linksIn: noteId } }
        }
      });
    }
    
    if (bulkOps.length > 0) {
      const result = await NotePage.bulkWrite(bulkOps, { ordered: false });
      
      // Verify all operations were successful
      if (result.modifiedCount !== (removedLinks.length + newLinks.length)) {
        throw new DatabaseError('Some link updates failed');
      }
    }

    return true;
  } catch (error) {
    if (error instanceof DatabaseError) {
      throw error;
    }
    throw new DatabaseError(`Failed to update links: ${error.message}`);
  }
}

// Helper function to validate links
async function validateLinks(noteId, linksOut) {
  try {
    const existingNotes = await NotePage.find({
      _id: { $in: linksOut },
      isDeleted: false
    }).select('_id');

    const existingIds = existingNotes.map(note => note._id.toString());
    const invalidLinks = linksOut.filter(id => !existingIds.includes(id.toString()));

    if (invalidLinks.length > 0) {
      throw new DatabaseError(`Invalid links found: ${invalidLinks.join(', ')}`);
    }

    return true;
  } catch (error) {
    if (error instanceof DatabaseError) {
      throw error;
    }
    throw new DatabaseError(`Failed to validate links: ${error.message}`);
  }
}

module.exports = { 
  updateBidirectionalLinks,
  validateLinks
};