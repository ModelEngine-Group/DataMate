
function log(message, type = "log", provided = 'console') {
    const providedFn = globalThis[provided] || console;
    if (providedFn && typeof providedFn[type] === 'function') {
        const invokeMethod = providedFn[type ?? 'log'];
        invokeMethod.call(providedFn, message);
    }
}

function addMockPrefix(urlPrefix, api) {
    const newMockApi = {};
    Object.keys(api).map(apiKey=>{
        newMockApi[apiKey] = urlPrefix + api[apiKey];
    });

    return new Proxy(newMockApi, {
        get(target, prop) {
            if (prop in target) {
                return target[prop];
            } else {
                throw new Error(`API ${String(prop)} is not defined.`);
            }
        }
    })
}

module.exports = {
    log,
    addMockPrefix,
};