import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const child = spawn(process.execPath, ['server.mjs'], {
  cwd: here,
  env: { ...process.env, PORT: '0', UW_API_KEY: '' },
  stdio: ['ignore', 'pipe', 'pipe'],
});

let output = '';
const baseUrl = await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error('Server did not start. Output: ' + output.slice(-500))), 8000);
  timer.unref();
  const read = chunk => {
    output += chunk.toString();
    const match = output.match(/Silicon Market Terminal: http:\/\/127\.0\.0\.1:(\d+)/);
    if (match) {
      clearTimeout(timer);
      resolve('http://127.0.0.1:' + match[1]);
    }
  };
  child.stdout.on('data', read);
  child.stderr.on('data', chunk => { output += chunk.toString(); });
  child.once('error', error => { clearTimeout(timer); reject(error); });
  child.once('exit', code => {
    if (code !== null) {
      clearTimeout(timer);
      reject(new Error('Server exited before listening (' + code + '). Output: ' + output.slice(-500)));
    }
  });
});

try {
  const statusResponse = await fetch(baseUrl + '/api/status');
  const status = await statusResponse.json();
  assert.equal(statusResponse.status, 200);
  assert.equal(status.server.port, Number(new URL(baseUrl).port));

  const response = await fetch(baseUrl + '/api/health/readiness');
  const readiness = await response.json();
  assert.equal(response.status, 200);
  assert.equal(readiness.schema, 'silicon.pipeline-readiness.v1');
  assert.ok(['available', 'partial', 'unavailable'].includes(readiness.state));
  assert.equal(readiness.freshness.status, 'unknown');
  assert.equal(readiness.gates.decisionEligible, false);
  assert.equal(readiness.gates.orderSubmissionEnabled, false);
  assert.equal(Object.hasOwn(readiness, 'marketValues'), false);
  assert.equal(Object.hasOwn(readiness, 'spot'), false);

  const queryResponse = await fetch(baseUrl + '/api/health/readiness?unexpected=1');
  assert.equal(queryResponse.status, 400);
  const postResponse = await fetch(baseUrl + '/api/health/readiness', { method: 'POST' });
  assert.equal(postResponse.status, 405);
  process.stdout.write('Silicon readiness route smoke: PASS (loopback, read-only, metadata-only)\n');
} finally {
  child.kill();
  await new Promise(resolve => child.once('exit', resolve));
}
