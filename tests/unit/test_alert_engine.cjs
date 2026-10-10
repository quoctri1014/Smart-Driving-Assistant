// Run with node tests/unit/test_alert_engine.cjs; reuse the project's TS compiler.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('../../web-app/node_modules/typescript');

for (const source of ['web-app/src/lib/driving/alert-engine.ts', 'mobile-app/lib/driving/alert-engine.ts']) {
  const filename = path.resolve(source);
  const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS },
  }).outputText;
  const module = new Module(filename);
  module._compile(compiled, filename);
  const derive = module.exports.deriveDrivingUIState;
  const road = { traffic_signs: [], speed_advice: { current_speed: 60, recommended_speed: 0, reason: 'Khoang cach' } };
  assert.equal(derive(road, null, false, true).priority, 'SPEED_WARNING');
  assert.equal(derive(road, null, false, true).recommendedSpeed, 0);
  const cabin = { drowsiness: { is_drowsy: true }, seatbelt: { seatbelt_on: null } };
  assert.equal(derive(null, cabin, true, false).priority, 'DROWSINESS');
  cabin.drowsiness.is_drowsy = false;
  assert.equal(derive(null, cabin, true, false).priority, 'UNAVAILABLE');
  cabin.seatbelt.seatbelt_on = false;
  assert.equal(derive(null, cabin, true, false).priority, 'SEATBELT_WARNING');
  cabin.driving_time = { should_rest: true, message: 'Rest now' };
  assert.equal(derive(null, cabin, true, false).priority, 'REST_REMINDER');
  assert.equal(derive(null, cabin, true, true).priority, 'UNAVAILABLE');
  console.log(`${source}: 7 assertions passed`);
}
