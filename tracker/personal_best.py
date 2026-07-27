from __future__ import annotations

from typing import Any, Mapping


def parse_score(value: object) -> int:
    """
    Safely convert a score-like value into a nonnegative integer.
    """
    try:
        score = int(value)
    except (TypeError, ValueError):
        return 0

    return max(score, 0)


def build_personal_bests(
    session_detail: Mapping[str, Any],
    career_high_score: object,
) -> dict[str, Any]:
    """
    Compare one session's final score with the career high score.
    """
    current_score = parse_score(
        session_detail.get("final_score")
    )

    career_best = parse_score(
        career_high_score
    )

    is_pb = (
        current_score > 0
        and current_score == career_best
    )

    return {
        "overall_score": {
            "current_score": current_score,
            "career_best": career_best,
            "is_pb": is_pb,
        }
    }