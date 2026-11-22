import { test } from 'node:test'
import assert from 'node:assert/strict'
import { trendMonths } from '../src/utils/format.js'

test('trends include the selected month and five previous months across a year boundary', () => {
  assert.deepEqual(trendMonths('2026-02'), ['2025-09', '2025-10', '2025-11', '2025-12', '2026-01', '2026-02'])
})
