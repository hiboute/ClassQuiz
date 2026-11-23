# SPDX-License-Identifier: MPL-2.0
"""Pure scoring and leaderboard logic for live games (no Redis, no I/O).

Kept free of imports from the rest of the app so it can be unit tested alone.
"""

from typing import Iterable

BASE_POINTS = 1000
POINTS_BY_SETTING = {"standard": BASE_POINTS, "double": 2 * BASE_POINTS, "none": 0}
# Answers faster than this get the full base points.
INSTANT_ANSWER_MS = 500
STREAK_STEP_BONUS = 100
STREAK_BONUS_CAP = 500


def base_points_for(points_setting: str | None) -> int:
    """Base points of a question from its `points` setting (default standard)."""
    if points_setting is None:
        return BASE_POINTS
    return POINTS_BY_SETTING.get(str(getattr(points_setting, "value", points_setting)), BASE_POINTS)


def calculate_score(time_taken_ms: float, time_limit_s: float | int | str, base: int = BASE_POINTS) -> int:
    """Kahoot-like score of a CORRECT answer.

    round(base * (1 - (t / T) / 2)), clamped to [base / 2, base]; t is the
    answer time and T the question time limit. Answers under 0.5 s get the
    full base. Never negative. A wrong answer scores 0: the caller does not
    call this for it.
    """
    if base <= 0:
        return 0
    try:
        limit_ms = float(time_limit_s) * 1000
    except (TypeError, ValueError):
        limit_ms = 0
    t = max(0.0, float(time_taken_ms))
    if t < INSTANT_ANSWER_MS or limit_ms <= 0:
        return base
    score = round(base * (1 - (t / limit_ms) / 2))
    return int(min(base, max(round(base / 2), score)))


def streak_bonus(streak: int, base: int = BASE_POINTS) -> int:
    """Bonus for a correct answer that brings the streak to `streak`.

    +100 per step beyond 1 (streak 2 -> +100, 3 -> +200 ...), capped at +500,
    and only on a question that awards points.
    """
    if base <= 0 or streak <= 1:
        return 0
    return min(STREAK_BONUS_CAP, STREAK_STEP_BONUS * (streak - 1))


def rank_players(scores: dict[str, float]) -> list[tuple[str, int]]:
    """Players sorted best first: score descending, then username for ties."""
    return sorted(((u, int(float(s))) for u, s in scores.items()), key=lambda p: (-p[1], p[0]))


def build_rank_updates(
    scores: dict[str, float],
    gained: dict[str, int],
    streaks: dict[str, int],
    usernames: Iterable[str] | None = None,
) -> tuple[list[dict], dict[str, dict]]:
    """Return (top 5 for the host screen, {username: rank_update payload}).

    `scores` are the total scores (leaderboard ZSET), `gained` the points each
    player got on this question, `streaks` the current answer streaks.
    """
    ranked = rank_players(scores)
    total_players = len(ranked)
    top5 = [{"username": u, "score": s, "gained": int(gained.get(u, 0))} for u, s in ranked[:5]]
    wanted = set(usernames) if usernames is not None else None
    updates: dict[str, dict] = {}
    for i, (username, total) in enumerate(ranked):
        if wanted is not None and username not in wanted:
            continue
        behind_username = None
        behind_gap = None
        if i > 0:
            behind_username, above_total = ranked[i - 1]
            behind_gap = above_total - total
        updates[username] = {
            "rank": i + 1,
            "total_players": total_players,
            "total": total,
            "gained": int(gained.get(username, 0)),
            "streak": int(streaks.get(username, 0)),
            "behind_username": behind_username,
            "behind_gap": behind_gap,
        }
    return top5, updates


def build_podium(scores: dict[str, float]) -> tuple[list[dict], dict[str, dict]]:
    """Return (top 3, {username: {rank, total}}) for the end of the game."""
    ranked = rank_players(scores)
    top3 = [{"rank": i + 1, "username": u, "score": s} for i, (u, s) in enumerate(ranked[:3])]
    own = {u: {"rank": i + 1, "total": s} for i, (u, s) in enumerate(ranked)}
    return top3, own
