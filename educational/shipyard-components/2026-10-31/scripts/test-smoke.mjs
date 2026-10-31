import { spawnSync } from 'node:child_process';
const files = [
  "tests/forecast-engines.test.mjs",
  "tests/research-adapters-freshness.test.mjs",
  "tests/live-aperture-producer.test.mjs",
  "tests/chartslector-synthetic.test.mjs",
  "tests/psychology-component.test.mjs"
];
const result = spawnSync(process.execPath, ['--test', ...files], { stdio: 'inherit' });
process.exit(result.status ?? 1);
