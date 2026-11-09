const assert = require('node:assert/strict');
const { test } = require('node:test');
const { loadSource, hookRunner, fakeClock } = require('./helpers.cjs');

const tick = () => new Promise(setImmediate);
const translate = key => key;

function requestFixture(fetch = async () => new Response('{"code":"0"}', { headers: { 'content-type': 'application/json' } })) {
  const instances = [];
  const loading = { count: 0, show() { this.count++; }, hide() { this.count--; } };
  class XHR extends EventTarget {
    constructor() { super(); this.upload = new EventTarget(); instances.push(this); }
    open(method, url) { this.method = method; this.url = url; }
    setRequestHeader() {}
    getResponseHeader() { return 'application/json'; }
    getAllResponseHeaders() { return ''; }
    send(body) { this.body = body; }
    abort() { this.emit('abort'); }
    emit(event) { this.dispatchEvent(new Event(event)); this.dispatchEvent(new Event('loadend')); }
    respond(status = 200, data = { code: '0' }) {
      this.status = status;
      this.statusText = String(status);
      this.responseText = JSON.stringify(data);
      this.emit('load');
    }
  }
  const source = loadSource('src/utils/request.ts', {
    antd: { message: { error() {} } },
    './loading': { __esModule: true, default: loading },
    '@/utils/errorConfigStore.ts': { errorConfigStore: { getMessage() {} } },
    '@/i18n': { __esModule: true, default: { language: 'zh' } },
  }, { fetch, XMLHttpRequest: XHR, localStorage: { getItem() { return null; } } });
  return { request: source.default, loading, instances };
}

test('concurrent requests release loading after both complete', async () => {
  const resolves = [];
  const fixture = requestFixture(() => new Promise(resolve => resolves.push(resolve)));
  const first = fixture.request.get('/one', null, { showLoading: true });
  const second = fixture.request.get('/two', null, { showLoading: true });
  await tick();
  assert.equal(fixture.loading.count, 1);
  const response = () => new Response('{"code":"0"}', { headers: { 'content-type': 'application/json' } });
  resolves[0](response());
  await first;
  assert.equal(fixture.loading.count, 1);
  resolves[1](response());
  await second;
  assert.equal(fixture.loading.count, 0);
  assert.equal(fixture.request.count, 0);
});

test('network and interceptor failures release loading', async () => {
  const fixture = requestFixture(async () => { throw new Error('offline'); });
  await assert.rejects(fixture.request.get('/offline', null, { showLoading: true }), /offline/);
  assert.equal(fixture.loading.count, 0);
  fixture.request.addRequestInterceptor(() => { throw new Error('interceptor failed'); });
  await assert.rejects(fixture.request.get('/fail', null, { showLoading: true }), /interceptor failed/);
  assert.equal(fixture.loading.count, 0);
});

for (const event of ['error', 'abort', 'timeout']) {
  test(`upload ${event} rejects and releases loading`, async () => {
    const fixture = requestFixture();
    const promise = fixture.request.post('/upload', new FormData(), { onUploadProgress() {}, showLoading: true });
    const rejection = assert.rejects(promise);
    await tick();
    assert.equal(fixture.instances[0].withCredentials, true);
    fixture.instances[0].emit(event);
    await rejection;
    assert.equal(fixture.loading.count, 0);
  });
}

test('XHR honors cancellation and successful uploads release loading', async () => {
  const fixture = requestFixture();
  const controller = new AbortController();
  const cancelled = fixture.request.post('/upload', new FormData(), { signal: controller.signal, onUploadProgress() {} });
  const rejection = assert.rejects(cancelled, { name: 'AbortError' });
  await tick();
  controller.abort();
  await rejection;
  const successful = fixture.request.post('/upload', new FormData(), { onUploadProgress() {}, showLoading: true });
  await tick();
  fixture.instances[1].respond();
  await successful;
  assert.equal(fixture.loading.count, 0);
});

test('HTTP 201/204 succeed while business failures still reject', async () => {
  for (const status of [201, 204]) {
    const fixture = requestFixture(async () => status === 204
      ? new Response(null, { status })
      : new Response('{"code":"200"}', { status, headers: { 'content-type': 'application/json' } }));
    await fixture.request.post('/create');
  }
  const fixture = requestFixture(async () => new Response('{"code":"failed","message":"rejected"}', { headers: { 'content-type': 'application/json' } }));
  await assert.rejects(fixture.request.get('/failed'), error => error.message === 'rejected');
});

function listFixture() {
  const runner = hookRunner();
  const clock = fakeClock();
  const calls = [];
  const messages = [];
  const message = { error: value => messages.push(value), warning: value => messages.push(value) };
  let fail = false;
  let loadingCount = 0;
  const useFetchData = loadSource('src/hooks/useFetchData.ts', {
    react: runner.react,
    antd: { App: { useApp: () => ({ message }) } },
    'react-i18next': { useTranslation: () => ({ t: translate }) },
    '@/utils/loading': { __esModule: true, default: {
      show() { loadingCount++; }, hide() { loadingCount--; }, hideAll() { loadingCount = 0; },
    } },
  }, clock).default;
  const fetch = async params => {
    calls.push(params);
    if (fail) throw fail === true ? new Error('offline') : fail;
    return { data: { content: [{ id: 'row' }], totalElements: 1 } };
  };
  return { runner, clock, calls, messages, setFail(value) { fail = value; }, get loadingCount() { return loadingCount; },
    render: () => runner.render(() => useFetchData(fetch, item => item)) };
}

test('template and evaluation filters reach the list query, including clearing built-in filters', async () => {
  const fixture = listFixture();
  let list = fixture.render();
  await fixture.clock.run(0);
  list.handleFiltersChange({ builtIn: ['true'], category: ['nlp'], dataType: ['TEXT'], labelingType: ['classification'], taskType: ['QA'], evalMethod: ['AUTO'] });
  list = fixture.render();
  await fixture.clock.run(0);
  const params = fixture.calls.at(-1);
  assert.equal(params.built_in, true);
  assert.equal(params.category, 'nlp');
  assert.equal(params.dataType, 'TEXT');
  assert.equal(params.labelingType, 'classification');
  assert.equal(params.taskType, 'QA');
  assert.equal(params.evalMethod, 'AUTO');
  list.handleFiltersChange({ builtIn: ['all'] });
  list = fixture.render();
  await fixture.clock.run(0);
  assert.equal(fixture.calls.at(-1).built_in, undefined);
  list.setSearchParams(previous => ({ ...previous, filter: {} }));
  fixture.render();
  await fixture.clock.run(0);
  assert.equal(fixture.messages.length, 0);
});

test('debounced search survives unrelated renders and resets pagination', async () => {
  const fixture = listFixture();
  let list = fixture.render();
  await fixture.clock.run(0);
  list.pagination.onChange(3, 12);
  list = fixture.render();
  await fixture.clock.run(0);
  list.handleKeywordChange('query');
  fixture.render();
  fixture.render();
  fixture.render();
  await fixture.clock.run(500);
  assert.equal(fixture.calls.at(-1).keyword, 'query');
  assert.equal(fixture.calls.at(-1).page, 0);
  assert.equal(fixture.calls.length, 3);
});

test('initial list query survives StrictMode effect remount', async () => {
  const fixture = listFixture();
  fixture.render();
  fixture.runner.strictRemount();
  await fixture.clock.run(0);
  assert.equal(fixture.calls.length, 1);
});

test('an expired login produces a warning and releases list loading', async () => {
  const fixture = listFixture();
  const list = fixture.render();
  fixture.setFail({ status: 401 });
  await list.fetchData();
  assert.equal(fixture.messages[0], 'hooks.fetchData.loginRequired');
  assert.equal(fixture.loadingCount, 0);
});

test('polling resumes after a failed manual refresh and background polling preserves other loading state', async () => {
  const fixture = listFixture();
  let list = fixture.render();
  await fixture.clock.run(0);
  list.startPolling();
  list = fixture.render();
  fixture.setFail(true);
  await list.fetchData();
  fixture.setFail(false);
  const before = fixture.calls.length;
  await fixture.clock.run(30000);
  assert.equal(fixture.calls.length, before + 1);
  assert.equal(fixture.loadingCount, 0);
  fixture.runner.result.stopPolling();
  assert.equal(fixture.clock.size, 0);
});

test('list API adapters translate UI search and filter names to backend parameters', async () => {
  const calls = [];
  const request = { get: async (url, params) => { calls.push({ url, params }); } };
  const ratio = loadSource('src/pages/RatioTask/ratio.api.ts', { '@/utils/request': request });
  const evaluation = loadSource('src/pages/DataEvaluation/evaluation.api.ts', { '@/utils/request': request });
  const annotation = loadSource('src/pages/DataAnnotation/annotation.api.ts', { '@/utils/request': request });
  await ratio.queryRatioTasksUsingGet({ keyword: 'ratio', status: 'COMPLETED', page: 2 });
  assert.equal(calls.at(-1).params.name, 'ratio');
  assert.equal(calls.at(-1).params.page, 2);
  assert.equal(calls.at(-1).params.status, 'COMPLETED');
  await evaluation.getPagedEvaluationTaskUsingGet({ keyword: 'eval', taskType: 'QA', evalMethod: 'AUTO' });
  assert.equal(calls.at(-1).params.name, 'eval');
  assert.equal(calls.at(-1).params.task_type, 'QA');
  assert.equal(calls.at(-1).params.eval_method, 'AUTO');
  await annotation.queryAnnotationTemplatesUsingGet({ built_in: false, dataType: 'TEXT' });
  assert.equal(calls.at(-1).params.builtIn, false);
  assert.equal(calls.at(-1).params.dataType, 'TEXT');
});

test('duplicate file and directory names show the conflict instead of throwing', async () => {
  const runner = hookRunner();
  const errors = [];
  const api = {
    renameDatasetFileUsingPut: async () => { throw new Error('already exists'); },
    renameDirectoryUsingPut: async () => { throw new Error('duplicate'); },
  };
  const useFilesOperation = loadSource('src/pages/DataManagement/Detail/useFilesOperation.ts', {
    react: runner.react,
    antd: { App: { useApp: () => ({ message: { error: value => errors.push(value.content), warning() {} } }) } },
    jszip: { __esModule: true, default: class {} },
    '../dataset.api': api,
    'react-router': { useParams: () => ({ id: 'dataset' }) },
  }).useFilesOperation;
  const operations = runner.render(() => useFilesOperation({ id: 'dataset' }));
  await operations.handleRenameFile({ id: 'file', fileName: 'old.txt' }, ' new.txt ');
  await operations.handleRenameDirectory('dir/', 'old', ' new ');
  assert.equal(errors.length, 2);
  assert.match(errors[0], /"new.txt" 已存在/);
  assert.match(errors[1], /"new" 已存在/);
});

test('cleaning tasks with missing or invalid execution dates still map for display', () => {
  const unit = loadSource('src/utils/unit.ts');
  const model = loadSource('src/pages/DataCleansing/cleansing.model.ts');
  const { mapTask } = loadSource('src/pages/DataCleansing/cleansing.const.tsx', {
    '@/utils/unit': unit,
    '@/pages/DataCleansing/cleansing.model': model,
    'lucide-react': { BrushCleaning: 'BrushCleaning', Layout: 'Layout' },
  });
  const task = { id: 'task', name: 'pending', status: 'PENDING', createdAt: '2026-11-06T08:00:00Z' };
  assert.equal(mapTask(task, translate).updatedAt, unit.formatDateTime(task.createdAt));
  assert.equal(mapTask({ ...task, finishedAt: 'invalid', updatedAt: '2026-11-06T10:00:00Z' }, translate).updatedAt, unit.formatDateTime('2026-11-06T10:00:00Z'));
  assert.equal(mapTask({ status: 'PENDING' }, translate).updatedAt, '');
});

function findElement(tree, predicate) {
  if (!tree || typeof tree !== 'object') return undefined;
  if (Array.isArray(tree)) return tree.map(child => findElement(child, predicate)).find(Boolean);
  if (predicate(tree)) return tree;
  return findElement(tree.props?.children, predicate);
}

test('ratio detail renders before loading and deletion returns to its task list', async () => {
  const runner = hookRunner();
  const deleted = [];
  const navigated = [];
  const Detail = loadSource('src/pages/RatioTask/Detail/RatioTaskDetail.tsx', {
    react: { ...runner.react, useEffect() {} },
    antd: { App: { useApp: () => ({ message: { success() {} } }) } },
    '@ant-design/icons': {},
    'react-i18next': { useTranslation: () => ({ t: translate }) },
    '@/components/DetailHeader': { __esModule: true, default: 'DetailHeader' },
    'react-router': { useParams: () => ({ id: 'ratio-1' }), useNavigate: () => path => navigated.push(path) },
    '@/pages/RatioTask/ratio.api': { deleteRatioTasksUsingDelete: async id => deleted.push(id) },
    '@/utils/request': {},
    '../ratio.const': {},
    './DataRatioChart': {}, './RatioDisplay': {}, './DataMetrics': {},
  }).default;
  const tree = runner.render(() => Detail());
  const header = findElement(tree, element => element.type === 'DetailHeader');
  await header.props.operations.find(operation => operation.key === 'delete').onClick();
  assert.deepEqual(deleted, ['ratio-1']);
  assert.deepEqual(navigated, ['/data/synthesis/ratio-task']);
});

test('cleaning file filters tolerate unfinished results and failed downloads show an error', async () => {
  const runner = hookRunner();
  const errors = [];
  const FileTable = loadSource('src/pages/DataCleansing/Detail/components/FileTable.tsx', {
    react: { ...runner.react, useEffect() {} },
    antd: { Table: 'Table', Button: 'Button', App: { useApp: () => ({ message: { error: value => errors.push(value) } }) } },
    'lucide-react': {},
    'react-router': { useParams: () => ({ id: 'cleaning-1' }) },
    '@/pages/DataCleansing/cleansing.model.ts': {},
    '@/pages/DataCleansing/cleansing.const.tsx': {},
    'react-i18next': { useTranslation: () => ({ t: translate }) },
  }, { fetch: async () => ({ ok: false }), console: { error() {} } }).default;
  const tree = runner.render(() => FileTable({ fetchTaskResult() {} }));
  const table = findElement(tree, element => element.type === 'Table');
  assert.equal(table.props.dataSource.length, 0);
  for (const column of table.props.columns.filter(column => column.onFilter)) {
    assert.equal(column.onFilter('text', {}), false);
  }
  const actions = table.props.columns.find(column => column.key === 'action').render('', {});
  const download = findElement(actions, element => element.type === 'Button' && element.props.children === 'dataCleansing.actions.download');
  await download.props.onClick();
  assert.equal(errors.length, 1);
});

test('cleaning logs can open while task details are still loading', () => {
  const runner = hookRunner();
  const model = loadSource('src/pages/DataCleansing/cleansing.model.ts');
  const Detail = loadSource('src/pages/DataCleansing/Detail/TaskDetail.tsx', {
    react: { ...runner.react, useEffect() {}, useState: initial => runner.react.useState(initial === 'basic' ? 'logs' : initial) },
    antd: { App: { useApp: () => ({ message: {} }) } },
    'lucide-react': {},
    '@ant-design/icons': {},
    '@/components/DetailHeader': { __esModule: true, default: 'DetailHeader' },
    'react-router': { useParams: () => ({ id: 'task' }), useNavigate: () => () => {} },
    '../cleansing.api': {}, '../cleansing.const': {},
    '@/pages/DataCleansing/cleansing.model': model,
    './components/BasicInfo': {}, './components/OperatorTable': {}, './components/FileTable': {},
    './components/LogsTable': { __esModule: true, default: 'LogsTable' },
    '@/utils/unit.ts': loadSource('src/utils/unit.ts'),
    'react-i18next': { useTranslation: () => ({ t: translate }) },
  }).default;
  const tree = runner.render(() => Detail());
  const logs = findElement(tree, element => element.type === 'LogsTable');
  assert.equal(logs.props.retryCount, 0);
  assert.equal(logs.props.taskName, '');
});

test('ratio configuration keeps selected dataset details across dataset pages', () => {
  const runner = hookRunner();
  const Create = loadSource('src/pages/RatioTask/Create/CreateRatioTask.tsx', {
    react: runner.react,
    antd: { Form: { useForm: () => [{}] } },
    'lucide-react': {},
    '@/pages/RatioTask/ratio.api.ts': {},
    'react-router': { useNavigate: () => () => {} },
    'react-i18next': { useTranslation: () => ({ t: translate }) },
    '@/pages/RatioTask/Create/components/SelectDataset.tsx': { __esModule: true, default: 'SelectDataset' },
    '@/pages/RatioTask/Create/components/BasicInformation.tsx': {},
    '@/pages/RatioTask/Create/components/RatioConfig.tsx': { __esModule: true, default: 'RatioConfig' },
    '@/utils/unit.ts': {},
  }).default;
  let tree = runner.render(() => Create());
  let selector = findElement(tree, element => element.type === 'SelectDataset');
  selector.props.onDatasetsChange([{ id: 'first', name: 'First page dataset' }]);
  selector.props.onSelectedDatasetsChange(['first']);
  tree = runner.render(() => Create());
  selector = findElement(tree, element => element.type === 'SelectDataset');
  selector.props.onDatasetsChange([{ id: 'second', name: 'Second page dataset' }]);
  tree = runner.render(() => Create());
  const config = findElement(tree, element => element.type === 'RatioConfig');
  assert.equal(config.props.selectedDatasets[0], 'first');
  assert.equal(config.props.datasets.find(dataset => dataset.id === 'first').name, 'First page dataset');
});

test('cancelling a file upload aborts its chunk and prevents remaining chunks', async () => {
  const runner = hookRunner();
  const errors = [];
  const chunks = [];
  const cancelled = [];
  const useUpload = loadSource('src/hooks/useSliceUpload.tsx', {
    react: runner.react,
    antd: { App: { useApp: () => ({ message: { error: value => errors.push(value) } }) } },
    'react-i18next': { useTranslation: () => ({ t: translate }) },
    '@/utils/file.util': { calculateSHA256: async () => 'checksum', checkIsFilesExist: async () => false },
  }, { AbortController, Event, CustomEvent, window: { dispatchEvent() {} }, console: { log() {}, error() {} } }).useFileSliceUpload;
  const options = {
    preUpload: async () => ({ data: 1 }),
    uploadChunk: async (id, form, config) => {
      chunks.push({ id, form, config });
      return new Promise((resolve, reject) => config.signal?.addEventListener('abort', () => reject(new DOMException('cancelled', 'AbortError')), { once: true }));
    },
    cancelUpload: async id => cancelled.push(id),
  };
  let upload = runner.render(() => useUpload(options, false));
  const task = upload.createTask({ dataset: { id: 'dataset', name: 'dataset' } });
  const promise = upload.handleUpload({ task, files: [{ name: 'file.txt', size: 2, slices: [new Blob(['a']), new Blob(['b'])] }] });
  await tick();
  assert.equal(chunks.length, 1);
  assert.equal(chunks[0].config.signal, task.controller.signal);
  upload = runner.render(() => useUpload(options, false));
  upload.removeTask({ ...upload.taskList[0], isCancel: true });
  await promise;
  assert.equal(chunks.length, 1);
  assert.equal(errors.length, 0);
  assert.deepEqual(cancelled, [1]);
});
