const API = require('../mock-apis.cjs');

const strongMatch = (req, res, next) => {
    res.strongMatch = () => {
        const { url } = req;
        const index = url.indexOf('?');
        const targetUrl = index !== -1 ? url.substring(0, index) : url;
        const isExistedUrl = Object.values(API).includes(targetUrl);
        return isExistedUrl;
    };
    next();
};
module.exports = strongMatch;