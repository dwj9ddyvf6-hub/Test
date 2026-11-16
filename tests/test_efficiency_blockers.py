"""EFF-1 blockers: cost-aware list scheduling in the worker pool.

Old behaviour: round-robin assignment in config order (i % size) — the
worker that drew the 33s saty_gpt_v02 ALSO carried ~half the remaining
roster serially, so the cycle makespan exceeded the single-sleeve
floor by the queue stacked behind it. New: longest-known-cost first,
each task to the least-loaded queue; costs learned from prior cycles.
Fail direction: schedule_tasks does not exist on the old tree (import
error) and the makespan case exceeds the bound under round-robin.
"""
import os, sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from desk3.pool import schedule_tasks, WorkerPool


def T(sid):
    return {"sleeve_id": sid, "module": "m", "snapshot_path": "p",
            "snapshot_hash": "h", "ctx": {}}


def makespan(queues, costs):
    return max(sum(costs[t["sleeve_id"]] for t in q) for q in queues if q)


class TestSchedule(unittest.TestCase):
    def test_big_task_does_not_stack_a_queue_behind_it(self):
        costs = {"big": 33.0}
        tasks = [T("big")]
        for i in range(14):
            sid = f"s{i}"
            costs[sid] = 1.0
            tasks.append(T(sid))
        queues = schedule_tasks(tasks, costs, 2)
        # round-robin in this order gives 33+7=40; list scheduling <= 34
        self.assertLessEqual(makespan(queues, costs), 34.0)
        self.assertEqual(sum(len(q) for q in queues), 15)

    def test_unknown_costs_still_assign_everything_balanced(self):
        tasks = [T(f"s{i}") for i in range(10)]
        queues = schedule_tasks(tasks, {}, 2)
        self.assertEqual(sum(len(q) for q in queues), 10)
        self.assertLessEqual(abs(len(queues[0]) - len(queues[1])), 1)

    def test_every_task_assigned_exactly_once(self):
        costs = {f"s{i}": float(i) for i in range(9)}
        tasks = [T(f"s{i}") for i in range(9)]
        queues = schedule_tasks(tasks, costs, 3)
        seen = [t["sleeve_id"] for q in queues for t in q]
        self.assertEqual(sorted(seen), sorted(costs))


class _FakeWorker:
    def __init__(self, pool):
        self.pool = pool

    def run_task(self, task, timeout_s):
        return {"sleeve_id": task["sleeve_id"], "status": "ok", "intents": []}


class TestCostLearning(unittest.TestCase):
    def test_pool_records_elapsed_costs_for_next_cycle(self):
        import desk3.pool as poolmod
        orig = poolmod._Worker
        poolmod._Worker = _FakeWorker
        try:
            pool = WorkerPool(size=2, state_root="/tmp/eff1_pool_state")
            pool.run([T("a"), T("b"), T("c")])
            self.assertIn("a", pool._costs)
            self.assertIn("b", pool._costs)
            self.assertGreaterEqual(pool._costs["a"], 0.0)
        finally:
            poolmod._Worker = orig


if __name__ == "__main__":
    unittest.main()
