const setHeader = require('./set-header-middleware.cjs');
const strongMatch = require('./strong-match-middleware.cjs');   
const sendJSON = require('./send-json-middleawre.cjs');
const errorHandle = require('./error-handle-middleware.cjs');

module.exports = {
    setHeader,
    strongMatch,
    sendJSON,   
    errorHandle,
};