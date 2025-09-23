const errorHandle = (err, req, res, next) => { 
    if(res.headersSent) {
        return next(err);
    }
    console.error('Server Error:', err.message);
    res.status(500).json({
        code: '500',
        msg: 'Internal Server Error',
        data: null,
    });
};

module.exports = errorHandle;
