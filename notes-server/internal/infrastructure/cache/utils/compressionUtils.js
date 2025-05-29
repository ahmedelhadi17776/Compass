const { promisify } = require('util');
const { gzip, gunzip } = require('zlib');
const { logger } = require('../../../../pkg/utils/logger');

const gzipAsync = promisify(gzip);
const gunzipAsync = promisify(gunzip);

async function compress(data) {
  try {
    const buffer = await gzipAsync(JSON.stringify(data));
    return buffer.toString('base64');
  } catch (error) {
    logger.error('Compression failed:', { error: error.message });
    return data;
  }
}

async function decompress(data) {
  try {
    const buffer = Buffer.from(data, 'base64');
    const decompressed = await gunzipAsync(buffer);
    return JSON.parse(decompressed.toString());
  } catch (error) {
    logger.error('Decompression failed:', { error: error.message });
    return data;
  }
}

module.exports = { compress, decompress }; 