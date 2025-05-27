const { DatabaseError } = require('../../../pkg/utils/errorHandler');
const NotePage = require('../../domain/notes/model');
const mongoose = require('mongoose');

// Helper function to update bi-directional links
const updateBidirectionalLinks = async (noteId, oldLinksOut = [], newLinksOut = []) => {
  try {
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
      const result = await mongoose.model('NotePage').bulkWrite(bulkOps, { ordered: false });
      
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
};

// Helper function to handle cascading deletes
const handleCascadingDelete = async (noteId) => {
  try {
    const note = await NotePage.findById(noteId);
    if (!note) return;

    const bulkOps = [];

    // Remove this note from linksIn of all linked notes
    if (note.linksOut.length > 0) {
      bulkOps.push({
        updateMany: {
          filter: { _id: { $in: note.linksOut } },
          update: { $pull: { linksIn: noteId } }
        }
      });
    }

    // Remove this note from linksOut of all notes that link to it
    if (note.linksIn.length > 0) {
      bulkOps.push({
        updateMany: {
          filter: { _id: { $in: note.linksIn } },
          update: { $pull: { linksOut: noteId } }
        }
      });
    }

    if (bulkOps.length > 0) {
      const result = await mongoose.model('NotePage').bulkWrite(bulkOps, { ordered: false });
      
      if (result.modifiedCount !== (note.linksOut.length + note.linksIn.length)) {
        throw new DatabaseError('Some cascading delete operations failed');
      }
    }

    return true;
  } catch (error) {
    if (error instanceof DatabaseError) {
      throw error;
    }
    throw new DatabaseError(`Failed to handle cascading delete: ${error.message}`);
  }
};

// Middleware to maintain bi-directional links
const maintainBidirectionalLinks = async (doc, next) => {
  try {
    if (doc.isModified('linksOut')) {
      const oldLinksOut = doc._oldLinksOut || [];
      await updateBidirectionalLinks(doc._id, oldLinksOut, doc.linksOut);
    }
    next();
  } catch (error) {
    next(error);
  }
};

// Middleware to handle cascading deletes
const handleDelete = async (doc, next) => {
  try {
    if (doc.isDeleted) {
      await handleCascadingDelete(doc._id);
    }
    next();
  } catch (error) {
    next(error);
  }
};

// Middleware to store old linksOut for comparison
const storeOldLinksOut = function(next) {
  if (this.isModified('linksOut')) {
    this._oldLinksOut = this.linksOut;
  }
  next();
};

module.exports = {
  maintainBidirectionalLinks,
  handleDelete,
  storeOldLinksOut,
  updateBidirectionalLinks,
  handleCascadingDelete
}; 