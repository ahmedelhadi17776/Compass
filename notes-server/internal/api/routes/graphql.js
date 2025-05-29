const express = require('express');
const { graphqlHTTP } = require('express-graphql');
const schema = require('../graphql');
const { formatGraphQLError } = require('../../../pkg/utils/errorHandler');
const { logger } = require('../../../pkg/utils/logger');

const router = express.Router();

router.use('/', graphqlHTTP({
  schema,
  graphiql: true,
  customFormatErrorFn: (error) => {
    const formattedError = formatGraphQLError(error);
    logger.error('GraphQL Error', {
      error: formattedError,
      path: error.path,
      locations: error.locations
    });
    return formattedError;
  }
}));

module.exports = router;