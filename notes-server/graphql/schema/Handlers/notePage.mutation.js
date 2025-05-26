const { GraphQLID, GraphQLString, GraphQLList, GraphQLBoolean } = require('graphql');
const NotePageType = require('../types/notePage.type');
const NotePage = require('../../../models/notePage.model');
const { updateBidirectionalLinks } = require('../../../utils/linkManager');

const notePageMutations = {
  addNotePage: {
    type: NotePageType,
    args: {
      userId: { type: GraphQLID },
      title: { type: GraphQLString },
      content: { type: GraphQLString },
      tags: { type: new GraphQLList(GraphQLString) },
      icon: { type: GraphQLString },
      linksOut: { type: new GraphQLList(GraphQLID) }
    },
    async resolve(parent, args) {
      const notePage = new NotePage({
        userId: args.userId,
        title: args.title,
        content: args.content,
        tags: args.tags,
        icon: args.icon,
        linksOut: args.linksOut || []
      });

      await notePage.save();

      if (args.linksOut?.length > 0) {
        await updateBidirectionalLinks(notePage._id, args.linksOut, []);
      }

      return notePage;
    }
  },
  updateNotePage: {
    type: NotePageType,
    args: {
      id: { type: GraphQLID },
      title: { type: GraphQLString },
      content: { type: GraphQLString },
      tags: { type: new GraphQLList(GraphQLString) },
      icon: { type: GraphQLString },
      favorited: { type: GraphQLBoolean },
      linksOut: { type: new GraphQLList(GraphQLID) }
    },
    async resolve(parent, args) {
      const note = await NotePage.findById(args.id);
      if (!note) throw new Error('Note not found');

      if (args.linksOut) {
        await updateBidirectionalLinks(args.id, args.linksOut, note.linksOut);
      }

      return NotePage.findByIdAndUpdate(
        args.id,
        {
          $set: {
            title: args.title,
            content: args.content,
            tags: args.tags,
            icon: args.icon,
            favorited: args.favorited,
            linksOut: args.linksOut
          }
        },
        { new: true }
      );
    }
  },
  deleteNotePage: {
    type: NotePageType,
    args: {
      id: { type: GraphQLID }
    },
    async resolve(parent, args) {
      const note = await NotePage.findByIdAndUpdate(
        args.id,
        { isDeleted: true },
        { new: true }
      );
      if (!note) throw new Error('Note not found');
      return note;
    }
  }
};

module.exports = notePageMutations; 