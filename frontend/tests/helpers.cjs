const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

function loadSource(file, imports = {}, globals = {}) {
  const root = process.env.DATAMATE_TEST_SOURCE_ROOT || path.resolve(__dirname, '..');
  const filename = path.join(root, file);
  const code = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    fileName: filename,
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true,
    },
  }).outputText;
  const exports = {};
  vm.runInNewContext(code, {
    exports,
    require(name) {
      if (Object.hasOwn(imports, name)) return imports[name];
      if (name === 'react/jsx-runtime') {
        const jsx = (type, props) => ({ type, props });
        return { jsx, jsxs: jsx, Fragment: 'Fragment' };
      }
      throw new Error(`Missing test dependency: ${name} in ${file}`);
    },
    console,
    setTimeout,
    clearTimeout,
    URLSearchParams,
    FormData,
    DOMException,
    ...globals,
  }, { filename });
  return exports;
}

// Exercise hooks, effects, and timer cancellation without requiring a DOM runtime.
function hookRunner() {
  const slots = [];
  let index = 0;
  let pending = [];
  let result;
  const changed = (old, next) => !old || !next || old.length !== next.length || old.some((value, i) => !Object.is(value, next[i]));
  const react = {
    useState(initial) {
      const key = index++;
      if (!slots[key]) slots[key] = { value: typeof initial === 'function' ? initial() : initial };
      return [slots[key].value, value => {
        slots[key].value = typeof value === 'function' ? value(slots[key].value) : value;
      }];
    },
    useRef(initial) {
      const key = index++;
      return (slots[key] ??= { current: initial });
    },
    useMemo(factory, deps) {
      const key = index++;
      if (changed(slots[key]?.deps, deps)) slots[key] = { deps, value: factory() };
      return slots[key].value;
    },
    useCallback(fn, deps) { return react.useMemo(() => fn, deps); },
    useEffect(effect, deps) {
      const key = index++;
      if (changed(slots[key]?.deps, deps)) {
        const previous = slots[key];
        const slot = slots[key] = { deps, effect };
        pending.push(() => { previous?.cleanup?.(); slot.cleanup = effect(); });
      }
    },
  };
  return {
    react,
    render(render) {
      index = 0;
      pending = [];
      result = render();
      pending.forEach(effect => effect());
      return result;
    },
    get result() { return result; },
    strictRemount() {
      const effects = slots.filter(slot => slot.effect);
      effects.forEach(slot => slot.cleanup?.());
      effects.forEach(slot => { slot.cleanup = slot.effect(); });
    },
    unmount() { slots.forEach(slot => slot.cleanup?.()); },
  };
}

function fakeClock() {
  let nextId = 1;
  const timers = new Map();
  return {
    setTimeout(callback, delay) { const id = nextId++; timers.set(id, { callback, delay }); return id; },
    clearTimeout(id) { timers.delete(id); },
    get size() { return timers.size; },
    async run(delay) {
      const ready = [...timers].filter(([, timer]) => timer.delay === delay);
      for (const [id, timer] of ready) {
        if (timers.delete(id)) await timer.callback();
      }
      await new Promise(setImmediate);
    },
  };
}

module.exports = { loadSource, hookRunner, fakeClock };
