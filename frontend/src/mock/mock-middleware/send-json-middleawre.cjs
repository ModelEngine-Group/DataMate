const sendJSON = (req, res, next) => {
    res.sendJSON = (
        data = null,
        { code = '0', msg = 'success', statusCode = 200, timeout = 0 } = {}
    ) => {
        const timer = setTimeout(() => {
            res.status(statusCode).json({
                code,
                msg,
                data,
            });
            clearTimeout(timer);
        }, timeout);
    };
    next();
};

module.exports = sendJSON;