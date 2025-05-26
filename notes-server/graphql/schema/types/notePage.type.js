const { GraphQLObjectType, GraphQLString, GraphQLID, GraphQLList, GraphQLBoolean } = require('graphql');
const NotePage = require('../../../models/notePage.model');

const EntityType = new GraphQLObjectType({
  name: 'Entity',
  fields: {
    type: { type: GraphQLString },
    refId: { type: GraphQLID }
  }
});

const NotePageType = new GraphQLObjectType({
  name: 'NotePage',
  fields: () => ({
    id: { type: GraphQLID },
    userId: { type: GraphQLID },
    title: { type: GraphQLString },
    content: { type: GraphQLString },
    linksOut: { 
      type: new GraphQLList(NotePageType),
      resolve(parent) {
        return NotePage.find({ _id: { $in: parent.linksOut } });
      }
    },
    linksIn: { 
      type: new GraphQLList(NotePageType),
      resolve(parent) {
        return NotePage.find({ _id: { $in: parent.linksIn } });
      }
    },
    entities: { type: new GraphQLList(EntityType) },
    tags: { type: new GraphQLList(GraphQLString) },
    isDeleted: { type: GraphQLBoolean },
    favorited: { type: GraphQLBoolean },
    icon: { type: GraphQLString },
    createdAt: { type: GraphQLString },
    updatedAt: { type: GraphQLString }
  })
});

module.exports = NotePageType; 