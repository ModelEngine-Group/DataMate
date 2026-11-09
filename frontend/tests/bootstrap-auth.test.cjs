const assert = require('node:assert/strict');
const { test } = require('node:test');
const { loadSource, fakeClock } = require('./helpers.cjs');

async function bootstrapFixture({
  session = null,
  authenticated,
  requireLogin = true,
  userStatus = 200,
  homeUrl = '',
  cachedHomeUrl = null,
  pathname = '/',
} = {}) {
  const clock = fakeClock();
  const requests = [];
  const loginModes = [];
  const events = [];
  const redirects = [];
  const cacheWrites = [];
  let rendered = false;
  const container = { innerHTML: '' };
  loadSource('src/main.tsx', {
    react: { StrictMode: 'StrictMode', Suspense: 'Suspense' },
    'react-dom/client': { createRoot: () => ({ render() { rendered = true; } }) },
    'react-router': { RouterProvider: 'RouterProvider' },
    './routes/routes': {},
    antd: { App: 'App', Spin: 'Spin', ConfigProvider: 'ConfigProvider' },
    './index.css': {},
    './components/TopLoadingBar': {},
    './components/AuthGuard': {},
    './store': { store: {} },
    'react-redux': { Provider: 'Provider' },
    './theme': {},
    '@/utils/errorConfigStore.ts': { errorConfigStore: { async loadConfig() {} } },
    '@/utils/systemParam': {
      getCachedHomePageUrl: () => cachedHomeUrl,
      setCachedHomePageUrl: value => cacheWrites.push(value),
    },
    '@/utils/request': { setRequireLoginMode: value => loginModes.push(value) },
    '@/i18n': {},
  }, {
    ...clock,
    document: { getElementById: () => container },
    localStorage: { getItem: key => key === 'session' ? session : null },
    window: {
      location: { pathname, replace: url => redirects.push(url) },
      dispatchEvent: event => events.push(event.type),
    },
    CustomEvent: class { constructor(type) { this.type = type; } },
    fetch: async (url, config) => {
      requests.push({ url, config });
      if (url === '/api/user/me') {
        const loggedIn = authenticated ?? (config.headers.Authorization === 'Bearer valid-jwt');
        return new Response(JSON.stringify({
          code: '0', data: { requireLogin, authenticated: loggedIn },
        }), { status: userStatus, headers: { 'content-type': 'application/json' } });
      }
      assert.equal(url, '/api/sys-param/sys.home.page.url');
      return new Response(JSON.stringify({ code: '0', data: { paramValue: homeUrl } }), {
        headers: { 'content-type': 'application/json' },
      });
    },
  });
  await new Promise(setImmediate);
  await clock.run(500);
  return { requests, loginModes, events, redirects, cacheWrites, rendered };
}

test('bootstrap restores a local JWT login on the home page without reopening login', async () => {
  const fixture = await bootstrapFixture({ session: JSON.stringify({ token: 'valid-jwt' }) });
  assert.equal(fixture.requests[0].config.headers.Authorization, 'Bearer valid-jwt');
  assert.equal(fixture.requests[0].config.credentials, 'include');
  assert.deepEqual(fixture.loginModes, [true]);
  assert.equal(fixture.rendered, true);
  assert.deepEqual(fixture.events, []);
  assert.deepEqual(fixture.redirects, []);
});

test('bootstrap distinguishes mandatory login from an already authenticated SSO session', async () => {
  const fixture = await bootstrapFixture({ authenticated: true });
  assert.equal(fixture.requests[0].config.credentials, 'include');
  assert.deepEqual(fixture.loginModes, [true]);
  assert.equal(fixture.rendered, true);
  assert.deepEqual(fixture.events, []);
});

test('bootstrap still prompts an unauthenticated user when login is required', async () => {
  const fixture = await bootstrapFixture();
  assert.equal(fixture.rendered, true);
  assert.deepEqual(fixture.events, ['show-login']);
  assert.equal(fixture.requests.length, 1);
});

test('bootstrap does not trust a rejected token merely because a session exists', async () => {
  const fixture = await bootstrapFixture({
    session: JSON.stringify({ token: 'expired-jwt' }), authenticated: false,
  });
  assert.deepEqual(fixture.events, ['show-login']);
  assert.deepEqual(fixture.loginModes, [true]);
});

test('bootstrap handles an explicit 401 as unauthenticated', async () => {
  const fixture = await bootstrapFixture({ userStatus: 401 });
  assert.deepEqual(fixture.events, ['show-login']);
  assert.deepEqual(fixture.loginModes, [true]);
});

test('bootstrap permits anonymous home access when login is disabled', async () => {
  const fixture = await bootstrapFixture({ requireLogin: false });
  assert.equal(fixture.rendered, true);
  assert.deepEqual(fixture.loginModes, [false]);
  assert.deepEqual(fixture.events, []);
});

test('bootstrap checks the configured home page with the authenticated JWT', async () => {
  const fixture = await bootstrapFixture({
    session: JSON.stringify({ token: 'valid-jwt' }), homeUrl: '/data/management',
  });
  assert.equal(fixture.requests[1].config.headers.Authorization, 'Bearer valid-jwt');
  assert.deepEqual(fixture.redirects, ['/data/management']);
  assert.equal(fixture.rendered, false);
  assert.deepEqual(fixture.events, []);
});

test('bootstrap clears a removed home URL instead of redirecting an authenticated user to its stale cache', async () => {
  const fixture = await bootstrapFixture({ authenticated: true, cachedHomeUrl: '/old-home' });
  assert.deepEqual(fixture.redirects, []);
  assert.deepEqual(fixture.cacheWrites, [null]);
  assert.equal(fixture.rendered, true);
  assert.deepEqual(fixture.events, []);
});

test('bootstrap ignores home redirects outside the root route while restoring the JWT', async () => {
  const fixture = await bootstrapFixture({
    session: JSON.stringify({ token: 'valid-jwt' }), pathname: '/data/management',
  });
  assert.equal(fixture.requests[0].config.headers.Authorization, 'Bearer valid-jwt');
  assert.equal(fixture.requests.length, 1);
  assert.equal(fixture.rendered, true);
  assert.deepEqual(fixture.events, []);
});

test('bootstrap treats malformed session storage as unauthenticated without crashing', async () => {
  const fixture = await bootstrapFixture({ session: 'invalid-json' });
  assert.deepEqual(fixture.events, ['show-login']);
  assert.equal(fixture.rendered, true);
});
