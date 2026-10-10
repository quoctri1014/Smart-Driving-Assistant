// Transport regression tests. No test records are written to application storage.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('../../web-app/node_modules/typescript');
const source = fs.readFileSync('web-app/src/hooks/useRoadDrivingSocket.ts', 'utf8');
function setup(token = 'test-token') {
  const state = [], sockets = [], timers = new Map();
  let timerId = 0;
  class Socket {
    static OPEN = 1;
    static CLOSING = 2;
    constructor(url) { this.url = url; this.readyState = 0; this.bufferedAmount = 0; this.sent = []; sockets.push(this); }
    send(data) { this.sent.push(data); }
    close() { this.readyState = 3; this.onclose?.({ code: 1000 }); }
    receive(message) { this.onmessage({ data: JSON.stringify(message) }); }
  }
  const context = {
    exports: {}, URL, WebSocket: Socket, Date,
    process: { env: { NEXT_PUBLIC_WS_URL: 'ws://localhost:8000/ws/v1' } },
    localStorage: { getItem: () => token },
    setTimeout: fn => { timers.set(++timerId, fn); return timerId; },
    clearTimeout: id => timers.delete(id),
    require: () => ({
      useState: value => { const index = state.push(value) - 1; return [value, next => { state[index] = next; }]; },
      useRef: current => ({ current }), useCallback: fn => fn, useEffect: () => {},
    }),
  };
  vm.runInNewContext(ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, context);
  return { hook: context.exports.useRoadDrivingSocket(), state, sockets };
}
const { hook, state, sockets } = setup();
hook.connect();
hook.connect();
assert.equal(sockets.length, 1, 'duplicate connect must not create another stream');
const socket = sockets[0];
assert.equal(new URL(socket.url).pathname, '/ws/v1/stream');
socket.readyState = 1;
hook.sendFrame('before-ready');
assert.equal(socket.sent.length, 0, 'TCP connection alone does not mean AI is ready');
assert.equal(state[0], 'CONNECTING');
socket.receive({ type: 'session_started' });
assert.equal(state[0], 'CONNECTED');
hook.sendFrame('first');
hook.sendFrame('dropped');
assert.deepEqual(socket.sent, ['first'], 'only one unacknowledged frame');
socket.receive({ type: 'detection_result', data: { frame_id: 1, vehicles: [] } });
assert.equal(state[1].frame_id, 1);
assert.equal(state[2], false);
hook.sendFrame('second');
assert.equal(socket.sent.length, 2);
socket.receive({ type: 'error', code: 'PIPELINE_ERROR' });
assert.match(state[3], /PIPELINE_ERROR/);
assert.equal(state[2], true);
hook.disconnect();
assert.equal(state[0], 'IDLE', 'intentional close must not become an error');
const unauthenticated = setup(null);
unauthenticated.hook.connect();
assert.equal(unauthenticated.state[0], 'ERROR');
assert.equal(unauthenticated.sockets.length, 0);
console.log('Road socket: 14 assertions passed');
