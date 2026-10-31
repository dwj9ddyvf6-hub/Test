import { spawnSync } from 'node:child_process';
const files = [
  "tests/component-labs.test.mjs",
  "tests/market-overview.test.mjs",
  "tests/forecast-engines.test.mjs",
  "tests/forecast-fe01-policy.test.mjs",
  "tests/forecast-fe01-producer.test.mjs",
  "tests/forecast-fe02-policy.test.mjs",
  "tests/forecast-fe02-producer.test.mjs",
  "tests/forecast-fe02-session-v2-policy.test.mjs",
  "tests/forecast-fe02-session-v2-producer.test.mjs",
  "tests/forecast-fe03-policy.test.mjs",
  "tests/forecast-fe03-producer.test.mjs",
  "tests/forecast-fe04-fe09-fe12-producers.test.mjs",
  "tests/forecast-fe04-fe09-fe12-source-builders.test.mjs",
  "tests/forecast-fe05-breadth-policy.test.mjs",
  "tests/forecast-fe06-policy.test.mjs",
  "tests/forecast-fe07-fe10-policy.test.mjs",
  "tests/forecast-fe07-fe10-producer.test.mjs",
  "tests/forecast-fe08-policy.test.mjs",
  "tests/forecast-fe08-producer.test.mjs",
  "tests/forecast-fe12-v3-policy.test.mjs",
  "tests/forecast-fe27-30-public.test.mjs",
  "tests/forecast-fe28-producer.test.mjs",
  "tests/live-aperture-parity.test.mjs",
  "tests/live-aperture-producer.test.mjs",
  "tests/research-adapters-freshness.test.mjs",
  "tests/chartslector-synthetic.test.mjs",
  "tests/psychology-component.test.mjs"
];
const result = spawnSync(process.execPath, ['--test', ...files], { stdio: 'inherit' });
process.exit(result.status ?? 1);
