import test from 'node:test';
import assert from 'node:assert/strict';
import { calendarAgeDaysInNewYork } from '../dist/research-adapters.mjs';

test('evidence context age uses the New York calendar date across UTC rollover', () => {
  const asOf = '2026-10-22';
  assert.equal(calendarAgeDaysInNewYork(asOf, new Date('2026-10-29T00:31:00.000Z')), 6);
  assert.equal(calendarAgeDaysInNewYork(asOf, new Date('2026-10-29T03:59:59.000Z')), 6);
  assert.equal(calendarAgeDaysInNewYork(asOf, new Date('2026-10-29T04:00:00.000Z')), 7);
});

test('evidence context age rejects malformed dates and invalid instants', () => {
  assert.equal(calendarAgeDaysInNewYork('2026-02-30', new Date('2026-10-29T00:31:00.000Z')), null);
  assert.equal(calendarAgeDaysInNewYork('not-a-date', new Date('2026-10-29T00:31:00.000Z')), null);
  assert.equal(calendarAgeDaysInNewYork('2026-10-22', new Date(Number.NaN)), null);
});

