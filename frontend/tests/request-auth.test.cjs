const assert = require('node:assert/strict');
const { test } = require('node:test');
const { loadSource, fakeClock, hookRunner } = require('./helpers.cjs');

function fixture({ session = JSON.stringify({ token: 'test-jwt' }), response, fetch, globals = {} } = {}) {
  const requests = [];
  const links = [];
  const blobs = [];
  const revoked = [];
  const events = [];
  const clock = fakeClock();
  const source = loadSource('src/utils/request.ts', {
    antd: { message: { error() {} } },
    './loading': { __esModule: true, default: { show() {}, hide() {} } },
    '@/utils/errorConfigStore.ts': { errorConfigStore: { getMessage() {} } },
    '@/i18n': { __esModule: true, default: { language: 'zh' } },
  }, {
    ...clock,
    fetch: async (url, config) => {
      requests.push({ url, config });
      return fetch ? fetch(url, config) : response ?? new Response(Uint8Array.of(0, 255, 13, 10), {
        headers: { 'content-type': 'application/octet-stream', 'content-disposition': 'attachment; filename="archive.tar"' },
      });
    },
    localStorage: { getItem: key => key === 'session' ? session : null, removeItem() {} },
    CustomEvent: class { constructor(type) { this.type = type; } },
    window: {
      dispatchEvent: event => events.push(event.type),
      URL: {
        createObjectURL(blob) { blobs.push(blob); return 'blob:download'; },
        revokeObjectURL: url => revoked.push(url),
      },
    },
    document: {
      createElement: () => ({ style: {}, click() { this.clicked = true; } }),
      body: { appendChild: link => links.push(link), removeChild: link => { link.removed = true; } },
    },
    ...globals,
  });
  source.setRequireLoginMode(true);
  return { ...source, requests, links, blobs, revoked, events, clock };
}

const downloadCases = [
  ['src/pages/OperatorMarket/operator.api.ts', 'downloadExampleOperatorUsingGet', ['example.tar'], '/api/operators/examples/download', 'example.tar'],
  ['src/pages/DataManagement/dataset.api.ts', 'downloadDatasetUsingGet', ['dataset'], '/api/data-management/datasets/dataset/files/download', 'archive.tar'],
  ['src/pages/DataManagement/dataset.api.ts', 'downloadDirectoryUsingGet', ['dataset', '中文/folder/'], '/api/data-management/datasets/dataset/files/directories/download?prefix=%E4%B8%AD%E6%96%87%2Ffolder%2F', 'folder.zip'],
  ['src/pages/DataManagement/dataset.api.ts', 'downloadFileByIdUsingGet', ['dataset', '中文/', 'file', 'data.txt'], '/api/data-management/datasets/dataset/files/file/download?prefix=%E4%B8%AD%E6%96%87%2F', 'data.txt'],
  ['src/pages/DataCleansing/cleansing.api.ts', 'downloadCleaningTaskFiles', ['task'], '/api/cleaning/tasks/task/result/download', 'task_task_files.zip'],
  ['src/pages/DataEvaluation/evaluation.api.ts', 'exportEvaluationReportUsingGet', ['report', 'PDF', 'report.pdf'], '/api/v1/evaluation/reports/report/export?format=PDF', 'report.pdf'],
  ['src/pages/DataAnnotation/annotation.api.ts', 'downloadAutoAnnotationResultUsingGet', ['task'], '/api/annotation/auto/task/download', 'archive.tar'],
];

for (const [file, method, args, url, filename] of downloadCases) {
  for (const session of [JSON.stringify({ token: 'test-jwt' }), null]) {
    test(`${method} sends ${session ? 'the JWT' : 'SSO cookies'} and saves the response bytes`, async () => {
      const f = fixture({ session });
      const api = loadSource(file, { '@/utils/request': f });
      await api[method](...args);
      assert.equal(f.requests.length, 1);
      assert.equal(f.requests[0].url, url);
      assert.equal(f.requests[0].config.method, 'GET');
      assert.equal(f.requests[0].config.credentials, 'include');
      assert.equal(f.requests[0].config.headers.Authorization, session ? 'Bearer test-jwt' : undefined);
      assert.equal(f.requests[0].url.includes('token='), false);
      assert.deepEqual(new Uint8Array(await f.blobs[0].arrayBuffer()), Uint8Array.of(0, 255, 13, 10));
      assert.equal(f.links.length, 1);
      assert.equal(f.links[0].href, 'blob:download');
      assert.equal(f.links[0].download, filename);
      assert.equal(f.links[0].clicked, true);
      assert.equal(f.links[0].removed, true);
      await f.clock.run(0);
      assert.deepEqual(f.revoked, ['blob:download']);
    });
  }
}

for (const action of ['download', 'preview']) {
  for (const status of [401, 200]) {
    test(`${action} rejects ${status === 401 ? 'HTTP 401' : 'business authentication errors'} before saving and requests login`, async () => {
      const f = fixture({ response: new Response('{"code":"common.0401","message":"expired"}', {
        status, headers: { 'content-type': 'application/json' },
      }) });
      await assert.rejects(f.download('/api/files/download', null, '', action), error => error.status === status);
      assert.deepEqual(f.events, ['show-login']);
      assert.equal(f.blobs.length, 0);
      assert.equal(f.links.length, 0);
    });
  }
}

for (const session of [JSON.stringify({ token: 'test-jwt' }), null]) {
  test(`file and collection log previews send ${session ? 'the JWT' : 'cookies'} and expose a revocable blob`, async () => {
    for (const [file, method, args, url] of [
      ['src/pages/DataManagement/dataset.api.ts', 'downloadFileByIdUsingGet', ['dataset', 'folder/', 'file', 'file.txt', 'preview'], '/api/data-management/datasets/dataset/files/file/download?prefix=folder%2F'],
      ['src/pages/DataCollection/collection.apis.ts', 'queryExecutionLogFileByIdUsingGet', ['execution'], '/api/data-collection/executions/execution/log'],
    ]) {
      const f = fixture({ session });
      const api = loadSource(file, { '@/utils/request': f });
      const preview = await api[method](...args);
      assert.equal(f.requests[0].url, url);
      assert.equal(f.requests[0].config.credentials, 'include');
      assert.equal(f.requests[0].config.headers.Authorization, session ? 'Bearer test-jwt' : undefined);
      assert.equal(preview.blobUrl, 'blob:download');
      assert.equal(preview.size, 4);
      assert.equal(f.links.length, 0);
      preview.revoke();
      assert.deepEqual(f.revoked, ['blob:download']);
    }
  });
}

test('REST methods and multipart requests retain authentication with custom headers', async () => {
  const f = fixture({ fetch: async () => new Response('{"code":"0"}', { headers: { 'content-type': 'application/json' } }) });
  const options = { headers: { Accept: 'application/json' } };
  await f.get('/api/list', { page: 1 }, options);
  await f.post('/api/create', { name: 'name' }, options);
  await f.put('/api/update', { name: 'name' }, options);
  await f.del('/api/delete', { ids: ['id'] }, options);
  await f.patch('/api/patch', { name: 'name' }, options);
  await f.post('/api/upload', new FormData(), options);
  assert.deepEqual(f.requests.map(({ config }) => config.method), ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'POST']);
  for (const { config } of f.requests) {
    assert.equal(config.headers.Authorization, 'Bearer test-jwt');
    assert.equal(config.credentials, 'include');
    assert.equal(config.headers.Accept, 'application/json');
  }
  assert.equal(f.requests[5].config.headers['Content-Type'], undefined);
});

test('failed and aborted downloads never create a browser download', async () => {
  for (const error of [new Error('offline'), new DOMException('cancelled', 'AbortError')]) {
    const f = fixture({ fetch: async () => { throw error; } });
    await assert.rejects(f.download('/api/files/download'), caught => caught === error);
    assert.equal(f.blobs.length, 0);
    assert.equal(f.links.length, 0);
  }
});

test('XHR uploads send the same JWT and cookies as fetch requests', async () => {
  const instances = [];
  class XHR extends EventTarget {
    constructor() {
      super();
      this.upload = new EventTarget();
      this.headers = {};
      instances.push(this);
    }
    open(method, url) { this.method = method; this.url = url; }
    setRequestHeader(key, value) { this.headers[key] = value; }
    getResponseHeader() { return 'application/json'; }
    getAllResponseHeaders() { return ''; }
    send(body) { this.body = body; }
  }
  const f = fixture({ globals: { XMLHttpRequest: XHR } });
  const form = new FormData();
  form.append('file', new Blob(['data']), 'file.txt');
  const promise = f.post('/api/operators/upload/chunk', form, { onUploadProgress() {} });
  await new Promise(setImmediate);
  const xhr = instances[0];
  assert.equal(xhr.url, '/api/operators/upload/chunk');
  assert.equal(xhr.method, 'POST');
  assert.equal(xhr.headers.Authorization, 'Bearer test-jwt');
  assert.equal(xhr.withCredentials, true);
  assert.equal(xhr.headers['Content-Type'], undefined);
  assert.equal(xhr.body, form);
  xhr.status = 200;
  xhr.statusText = 'OK';
  xhr.responseText = '{"code":"0"}';
  xhr.dispatchEvent(new Event('load'));
  xhr.dispatchEvent(new Event('loadend'));
  await promise;
});

for (const status of [200, 401]) {
  test(`DeerFlow availability checks send authentication and clear the timeout on HTTP ${status}`, async () => {
    const f = fixture({ response: new Response('{}', { status, headers: { 'content-type': 'application/json' } }) });
    const runner = hookRunner();
    const navigated = [];
    const location = { href: '/' };
    const Home = loadSource('src/pages/Home/Home.tsx', {
      react: runner.react,
      'react-router': { useNavigate: () => url => navigated.push(url) },
      antd: { Card: 'Card', Dropdown: 'Dropdown', Button: 'Button' },
      'lucide-react': {},
      '../Layout/Menu.tsx': { features: [], menuItems: [] },
      'react-i18next': { useTranslation: () => ({ t: key => key }) },
      '@/i18n': { __esModule: true, default: { language: 'zh' } },
      '@/utils/request': f,
    }, { ...f.clock, AbortController, window: { location }, console: { error() {} } }).default;
    function find(tree) {
      if (!tree || typeof tree !== 'object') return;
      if (Array.isArray(tree)) return tree.map(find).find(Boolean);
      if (tree.props?.onClick && Array.isArray(tree.props.children) && tree.props.children.includes('home.hero.chatAssistantButton')) return tree;
      return find(tree.props?.children);
    }
    const tree = runner.render(() => Home());
    await find(tree).props.onClick();
    assert.equal(f.requests[0].url, '/deer-flow-backend/config');
    assert.equal(f.requests[0].config.headers.Authorization, 'Bearer test-jwt');
    assert.equal(f.requests[0].config.credentials, 'include');
    assert.equal(f.requests[0].config.cache, 'no-store');
    assert.equal(f.clock.size, status === 401 ? 1 : 0); // 401 retains only the login prompt debounce.
    assert.equal(location.href, status === 200 ? '/chat' : '/');
    assert.deepEqual(navigated, status === 401 ? ['/chat'] : []);
  });
}
