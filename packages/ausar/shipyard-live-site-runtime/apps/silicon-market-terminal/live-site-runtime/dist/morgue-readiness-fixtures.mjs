import assert from 'node:assert/strict';
import { summarizeMorgueReadiness, summarizeMorgueSnapshot } from './morgue-adapter.mjs';

const generated = '2026-10-28T14:00:00.000Z';
const evaluated = '2026-10-28T15:00:00.000Z';
const feed = {
  generated_at_utc: generated,
  as_of_session: '2026-10-27',
  map: {}, tape: {}, scorecard: {}, studies: {}, squeeze: {},
  wall_validation: {}, flow: {}, chain: {}, lanes: {}, board: {},
};
const snapshot = summarizeMorgueSnapshot(JSON.stringify(feed), generated);
const readiness = summarizeMorgueReadiness(snapshot, { evaluatedAtUtc: evaluated });

assert.equal(readiness.schema, 'silicon.pipeline-readiness.v1');
assert.equal(readiness.state, 'available');
assert.equal(readiness.artifactStatus, 'available');
assert.equal(readiness.snapshot.ageSeconds, 3600);
assert.equal(readiness.snapshot.presentSectionCount, 10);
assert.equal(readiness.snapshot.expectedSectionCount, 10);
assert.equal(readiness.freshness.status, 'unknown');
assert.equal(readiness.freshness.maximumAgeSeconds, null);
assert.equal(readiness.gates.decisionEligible, false);
assert.equal(readiness.gates.performanceClaimEligible, false);
assert.equal(readiness.gates.orderSubmissionEnabled, false);
assert.equal(Object.hasOwn(readiness, 'marketValues'), false);

const partial = summarizeMorgueSnapshot(JSON.stringify({
  generated_at_utc: generated,
  as_of_session: '2026-10-27',
  map: {},
}), generated);
assert.equal(summarizeMorgueReadiness(partial, { evaluatedAtUtc: evaluated }).state, 'partial');

const missing = summarizeMorgueReadiness(null, {
  evaluatedAtUtc: evaluated,
  artifactStatus: 'missing',
});
assert.equal(missing.state, 'unavailable');
assert.equal(missing.artifactStatus, 'missing');
assert.equal(missing.snapshot, null);
assert.throws(() => summarizeMorgueReadiness(snapshot, { evaluatedAtUtc: '2026-10-28' }), /timezone offset/);

process.stdout.write('Morgue readiness fixtures: PASS (freshness unknown and decision gates fail closed)\n');
