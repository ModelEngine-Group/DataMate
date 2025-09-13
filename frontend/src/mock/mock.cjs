const express = require('express');
const fs = require('fs-extra');
const path = require('path');
const bodyParser = require('body-parser');
const { genExpressSession } = require('./mock-core/session-helper.cjs');
const {
    setHeader,
    sendJSON,
    strongMatch,
    errorHandle,
} = require('./mock-middleware/index.cjs');


const { loadAllMockModules } = require('./mock-core/module-loader.cjs');
const { log } = require('./mock-core/util.cjs');

const app = express();
const router = express.Router();

const argv = require('minimist')(process.argv.slice(2));
const deployUrl = argv['deploy-url'] || '/';
const deployPath = argv['deploy-path'] || '/';
const port = argv.port || 8002;
const env = argv.env || 'development';

// app静态文件实际目录
const deployAppPath = path.join(__dirname, deployPath);
preStartCheck(deployAppPath);

app.use(setHeader);

// 提供静态文件服务
app.use(deployUrl, express.static(deployAppPath));
app.use(bodyParser.json({limit: '1mb'}));
app.use(bodyParser.urlencoded({ extended: false, limit: '1mb' })); 
app.use(sendJSON);
app.use(strongMatch);
app.use(genExpressSession());

const mockDir = path.join(__dirname, '/mock-seed');
loadAllMockModules(router, mockDir);
app.use(deployUrl, router);
app.use(errorHandle);

app.get('/', (req, res) => {
    res.sendFile('default response', { root: deployAppPath });
});

app.listen(port, function() {
    log(`Mock server is running at http://localhost:${port}${deployUrl} in ${env} mode`);
})

function preStartCheck(deployAppPath) {
    if(!fs.existsSync(deployAppPath)) {
        log(`Error: The path ${deployAppPath} does not exist. Please build the frontend application first.`, 'error');
        process.exit(1);
    }   
}