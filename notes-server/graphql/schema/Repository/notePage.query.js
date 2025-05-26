const { GraphQLID, GraphQLList, GraphQLString } = require('graphql');
const NotePageType = require('../types/notePage.type');
const NotePage = require('../../../models/notePage.model');

const notePageQueries = {
  notePage: {
    type: NotePageType,
    args: { id: { type: GraphQLID } },
    async resolve(parent, args, context) {
      const note = await NotePage.findOne({
        _id: args.id,
        isDeleted: false
      });
      if (!note) throw new Error('Note not found');
      return note;
    }
  },
  notePages: {
    type: new GraphQLList(NotePageType),
    args: { 
      userId: { type: GraphQLID },
      searchQuery: { type: GraphQLString }
    },
    async resolve(parent, args) {
      const query = { 
        userId: args.userId,
        isDeleted: false
      };

      if (args.searchQuery) {
        query.$text = { $search: args.searchQuery };
        return NotePage.find(query)
          .select('title content tags favorited icon createdAt updatedAt')
          .sort({ score: { $meta: 'textScore' } });
      }

      return NotePage.find(query)
        .select('title content tags favorited icon createdAt updatedAt');
    }
  }
};

module.exports = notePageQueries; 