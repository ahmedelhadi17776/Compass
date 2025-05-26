const NotePage = require('../models/notePage.model');

async function updateBidirectionalLinks(noteId, newLinksOut, oldLinksOut = []) {
  // Remove this note from linksIn of notes that are no longer linked
  const removedLinks = oldLinksOut.filter(link => !newLinksOut.includes(link.toString()));
  if (removedLinks.length > 0) {
    await NotePage.updateMany(
      { _id: { $in: removedLinks } },
      { $pull: { linksIn: noteId } }
    );
  }
  
  // Add this note to linksIn of newly linked notes
  const newLinks = newLinksOut.filter(link => !oldLinksOut.map(l => l.toString()).includes(link.toString()));
  if (newLinks.length > 0) {
    await NotePage.updateMany(
      { _id: { $in: newLinks } },
      { $addToSet: { linksIn: noteId } }
    );
  }
}

module.exports = { updateBidirectionalLinks }; 