import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { encodeAction } from 'wedgie-actions/protocol';

const text = encodeAction('starproof', { origin: 'https://starproof-wedgie.vercel.app', session: 'a'.repeat(32), challenge: 'b'.repeat(32), chip: 'c'.repeat(64), action: 'launch', from: 'sol', target: 'sol', cost: 0, sequence: 0, expires: 1900000000, nonce: 'd'.repeat(64) });
test('device acknowledges cancellation and never signs or accepts host approval', () => {
  assert.match(execFileSync('python3', ['test/device-cancel.py'], { input: JSON.stringify({ text }), encoding: 'utf8' }), /device request cancellation OK/);
});
test('all destination and artifact previews preserve firmware confirmation controls', () => {
  assert.match(execFileSync('python3', ['test/device-art.py'], { encoding: 'utf8' }), /device art preserves controls OK/);
});
test('device accepts production origin and rejects lookalikes and altered refuel costs', () => {
  const code = `import sys,json\nsys.path.insert(0,'device')\nfrom starproof_protocol import parse_action\nt=json.load(sys.stdin)['text']\nassert parse_action(t)['action']=='launch'\nfor bad in (t.replace('starproof-wedgie.vercel.app','starproof-wedgie.vercel.app.evil.test'),t.replace('cost=0','cost=99')):\n try: parse_action(bad)\n except ValueError: pass\n else: raise AssertionError('unsafe payload accepted')\nprint('protocol OK')`;
  assert.match(execFileSync('python3', ['-c', code], { input: JSON.stringify({ text }), encoding: 'utf8' }), /protocol OK/);
});

test('fuel prices follow distance and free scavenging stays in the current system', () => {
  const code = `import sys,json\nsys.path.insert(0,'device')\nfrom starproof_protocol import parse_action,jump_cost\nt=json.load(sys.stdin)['text']\nassert jump_cost('sol','kepler')==2\nassert jump_cost('sol','moss')==8\nassert parse_action(t.replace('action=launch','action=refuel').replace('cost=0','cost=4'))['cost']=='4'\nassert parse_action(t.replace('action=launch','action=scavenge'))['action']=='scavenge'\nfor bad in (t.replace('action=launch','action=refuel').replace('cost=0','cost=3'),t.replace('action=launch','action=scavenge').replace('target=sol','target=kepler')):\n try: parse_action(bad)\n except ValueError: pass\n else: raise AssertionError('invalid fuel action accepted')\nprint('fuel rules OK')`;
  assert.match(execFileSync('python3', ['-c', code], { input: JSON.stringify({ text }), encoding: 'utf8' }), /fuel rules OK/);
});
