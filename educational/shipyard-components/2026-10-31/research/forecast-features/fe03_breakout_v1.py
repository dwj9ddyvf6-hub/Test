#!/usr/bin/env python3
"""Independent FE03 NEW-policy oracle; synthetic test/reference use only."""
from __future__ import annotations

import json
import math
import statistics
import sys

MIN_EPISODES = 20


def episode_start(rows: list[dict], u: int) -> bool:
    level = max(row["h"] for row in rows[u - 20:u])
    previous_level = max(row["h"] for row in rows[u - 21:u - 1])
    return rows[u]["c"] > level and rows[u - 1]["c"] <= previous_level


def calculate(rows: list[dict]) -> dict:
    if len(rows) < 505:
        raise ValueError("invalid_daily_history")
    t = 504
    level = lambda u: max(row["h"] for row in rows[u - 20:u])
    starts_recent = [u for u in range(t - 5, t + 1) if episode_start(rows, u)]
    candidate = starts_recent[-1] if starts_recent else None
    matured = [u for u in range(21, t - 4) if episode_start(rows, u)]
    candidate_id = f"SPY:{rows[candidate]['date']}" if candidate is not None else None
    matured = [u for u in matured if f"SPY:{rows[u]['date']}" != candidate_id]
    false_count = sum(any(row["c"] < level(u) for row in rows[u + 1:u + 6]) for u in matured)
    history = {
        "eligible_episode_date_slots": t - 5 - 21 + 1,
        "eligible_trigger_start_index": 21,
        "eligible_trigger_end_index": t - 5,
        "matured_episode_count": len(matured),
        "false_break_count": false_count,
        "candidate_episode_excluded": candidate is not None and any(
            f"SPY:{rows[u]['date']}" == candidate_id for u in range(21, t - 4) if episode_start(rows, u)
        ),
    }
    if candidate is None:
        return {"status": "no_setup", "history": history}
    frozen = level(candidate)
    post = rows[candidate + 1:t + 1]
    if rows[t]["c"] < frozen:
        return {"status": "level_invalidated", "history": history}
    if len(post) < 3:
        return {"status": "acceptance_not_mature", "history": history}
    if len(matured) < MIN_EPISODES:
        return {"status": "insufficient_mature_episode_sample", "history": history}
    distances = [math.log(row["c"] / level(i)) for i, row in enumerate(rows[:t + 1]) if i >= 20]
    # Indexed lookup is deliberately recomputed in this independent oracle.
    def d(i: int) -> float:
        return math.log(rows[i]["c"] / max(row["h"] for row in rows[i - 20:i]))
    prior_distance = [d(i) for i in range(candidate - 252, candidate)]
    mean_distance = statistics.fmean(prior_distance)
    sd_distance = statistics.pstdev(prior_distance)
    volume_prior = [math.log1p(rows[i]["v"]) for i in range(candidate - 20, candidate)]
    mean_volume = statistics.fmean(volume_prior)
    sd_volume = statistics.pstdev(volume_prior)
    acceptance_count = sum(row["c"] >= frozen for row in post)
    features = {
        "break_distance_z": (d(candidate) - mean_distance) / sd_distance,
        "acceptance": acceptance_count / len(post),
        "volume_surprise_z": (math.log1p(rows[candidate]["v"]) - mean_volume) / sd_volume,
        "false_break_rate": false_count / len(matured),
    }
    return {"status": "computed", "features": features, "history": history,
            "acceptance_numerator": acceptance_count, "acceptance_denominator": len(post)}


def main() -> None:
    rows = json.load(sys.stdin)
    print(json.dumps(calculate(rows), separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    main()
