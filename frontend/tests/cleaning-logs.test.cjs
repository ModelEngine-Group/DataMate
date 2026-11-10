const assert = require('node:assert/strict');
const { test } = require('node:test');
const { loadSource } = require('./helpers.cjs');

const tick = () => new Promise(setImmediate);

function fixture(fetch, session = JSON.stringify({ token: 'test-jwt' })) {
  const events = [];
  const request = loadSource('src/utils/request.ts', {
    antd: { message: { error() {} } },
    './loading': { __esModule: true, default: { show() {}, hide() {} } },
    '@/utils/errorConfigStore.ts': { errorConfigStore: { getMessage() {} } },
    '@/i18n': { __esModule: true, default: { language: 'zh' } },
  }, {
    fetch,
    localStorage: { getItem: key => key === 'session' ? session : null, removeItem() {} },
    window: { dispatchEvent: event => events.push(event.type) },
    CustomEvent: class { constructor(type) { this.type = type; } },
  });
  request.setRequireLoginMode(true);
  const api = loadSource('src/pages/DataCleansing/cleansing.api.ts', {
    '@/utils/request': request,
  }, { AbortController, TextDecoder });
  return { api, events };
}

test('log stream sends the JWT header and delivers split UTF-8 SSE messages before EOF', async () => {
  let pending;
  let body;
  let cancelled = false;
  const { api } = fixture(async (url, config) => {
    pending = { url, config };
    return new Response(new ReadableStream({
      start(controller) { body = controller; },
      cancel() { cancelled = true; },
    }), { headers: { 'content-type': 'text/event-stream' } });
  });
  const messages = [];
  const errors = [];
  const stream = api.streamCleaningTaskLog('task-1', 2);
  stream.onmessage = event => {
    messages.push(event.data);
    if (event.data.includes('[END_OF_STREAM]')) stream.close();
  };
  stream.onerror = error => errors.push(error);
  await tick();
  assert.equal(pending.url, '/api/cleaning/tasks/task-1/log/stream?retry_count=2');
  assert.equal(pending.config.headers.Authorization, 'Bearer test-jwt');
  assert.equal(pending.config.credentials, 'include');
  assert.equal(pending.config.headers.Accept, 'text/event-stream');
  assert.equal(pending.url.includes('token='), false);

  const encoded = new TextEncoder().encode(': heartbeat\r\ndata: {"message":"日志"}\r\n\r\n');
  for (const byte of encoded) body.enqueue(Uint8Array.of(byte));
  await tick();
  assert.deepEqual(messages, ['{"message":"日志"}']);
  body.enqueue(new TextEncoder().encode('data: {"message":"[END_OF_STREAM]"}\n\n'));
  await tick();
  assert.equal(messages.length, 2);
  assert.equal(pending.config.signal.aborted, true);
  assert.equal(cancelled, true);
  assert.deepEqual(errors, []);
});

test('closing a log stream aborts its request without reporting an error', async () => {
  let signal;
  const { api } = fixture((_url, config) => new Promise((_resolve, reject) => {
    signal = config.signal;
    signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
  }));
  const errors = [];
  const stream = api.streamCleaningTaskLog('task-1');
  stream.onerror = error => errors.push(error);
  await tick();
  stream.close();
  await tick();
  assert.equal(signal.aborted, true);
  assert.deepEqual(errors, []);
});

test('log downloads send authentication and preserve the downloaded bytes', async () => {
  const bytes = Uint8Array.of(0, 255, 10, 13, 65);
  const { api } = fixture(async (url, config) => {
    assert.equal(url, '/api/cleaning/tasks/task-1/log/1/download');
    assert.equal(config.headers.Authorization, 'Bearer test-jwt');
    return new Response(bytes, { headers: { 'content-type': 'application/octet-stream' } });
  });
  const blob = await api.downloadCleaningTaskLog('task-1', 1);
  assert.deepEqual(new Uint8Array(await blob.arrayBuffer()), bytes);
});

test('stream and download authentication failures use the shared login handling', async () => {
  const { api, events } = fixture(async () => new Response(
    JSON.stringify({ code: 'common.0401', message: 'expired' }),
    { status: 401, headers: { 'content-type': 'application/json' } },
  ));
  const error = await new Promise(resolve => {
    const stream = api.streamCleaningTaskLog('task-1');
    stream.onerror = resolve;
  });
  assert.equal(error.status, 401);
  assert.deepEqual(events, ['show-login']);
  await assert.rejects(api.downloadCleaningTaskLog('task-1'), error => error.status === 401);
});

test('log streams work without a session when login is optional', async () => {
  const { api } = fixture(async (_url, config) => {
    assert.equal(config.headers.Authorization, undefined);
    return new Response('data: done\n\n', { headers: { 'content-type': 'text/event-stream' } });
  }, null);
  const messages = [];
  await new Promise(resolve => {
    const stream = api.streamCleaningTaskLog('task-1');
    stream.onmessage = event => messages.push(event.data);
    stream.onerror = resolve;
  });
  assert.deepEqual(messages, ['done']);
});
