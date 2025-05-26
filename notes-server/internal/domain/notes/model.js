const mongoose = require('mongoose');
const { Schema, ObjectId } = mongoose;

const NotePageSchema = new Schema({
  userId: { type: ObjectId, ref: 'User', required: true, index: true },
  title: { type: String, required: true },
  content: { type: String, default: '' },
  linksOut: [{ type: ObjectId, ref: 'NotePage' }],
  linksIn: [{ type: ObjectId, ref: 'NotePage' }],
  entities: [{
    type: { type: String, enum: ['idea', 'tasks', 'person', 'todos'], required: true },
    refId: { type: ObjectId }
  }],
  template: { type: ObjectId, ref: 'Template' },
  tags: [{ type: String, index: true }],
  isDeleted: { type: Boolean, default: false },
  favorited: { type: Boolean, default: false },
  icon: { type: String }
}, {
  timestamps: true
});

// Full-text search on title & content
NotePageSchema.index({ title: 'text', content: 'text' });

module.exports = mongoose.model('NotePage', NotePageSchema); 