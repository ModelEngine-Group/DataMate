const fs = require('fs');

function loadAllMockModules(router, pathDir) {
    if (!fs.existsSync(pathDir)) {
        throw new Error(`Mock directory ${pathDir} does not exist.`);
    }

    const files = fs.readdirSync(pathDir);
    files.forEach(file => {
        const filePath = `${pathDir}/${file}`;
        if(fs.lstatSync(filePath).isDirectory()) {
            loadAllMockModules(router, filePath);
        } else {
            let fileNameModule = file.replace('/\.js\b$/', '');
            let module = require(`${pathDir}/${fileNameModule}`);
            if(typeof module === 'function' && module.length === 1) {
                module(router);
            }
        }
    }); 
}

module.exports = {
    loadAllMockModules,
};