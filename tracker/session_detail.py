from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    """
    Read a CSV file into a list of dictionaries.

    Missing files and malformed rows are treated as empty data rather than
    crashing the dashboard.
    """
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))
    except (OSError, csv.Error):
        return []


def parse_float(value: object, default: float = 0.0) -> float:
    """
    Parse a floating-point value safely.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value: object, default: int = 0) -> int:
    """
    Parse an integer safely.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def format_board(level: int, board_position: int) -> str:
    """
    Format a Donkey Kong board as level-position, such as 2-1.
    """
    if level <= 0 or board_position <= 0:
        return "Unknown"

    return f"{level}-{board_position}"



def build_board_splits(
    events: list[dict[str, Any]],
    duration_seconds: float,
) -> list[dict[str, Any]]:
    """
    Build per-board timing segments from board starts and transitions.

    A completed split begins with the first board_start after the previous
    transition and ends at the next level_transition. Any board still active
    when telemetry ends is included as an incomplete split.
    """
    board_splits: list[dict[str, Any]] = []
    active_start: dict[str, Any] | None = None

    for event in sorted(
        events,
        key=lambda item: float(item["elapsed_seconds"]),
    ):
        event_name = event["event"]

        if event_name == "board_start":
            if active_start is None:
                active_start = event
            continue

        if (
            event_name != "level_transition"
            or active_start is None
        ):
            continue

        start_seconds = float(
            active_start["elapsed_seconds"]
        )
        end_seconds = float(event["elapsed_seconds"])

        board_splits.append(
            {
                "board": active_start["board"],
                "screen_name": active_start["screen_name"],
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "duration_seconds": max(
                    0.0,
                    end_seconds - start_seconds,
                ),
                "score_start": int(active_start["score"]),
                "score_end": int(event["score"]),
                "score_gained": max(
                    0,
                    int(event["score"])
                    - int(active_start["score"]),
                ),
                "completed": True,
            }
        )

        active_start = None

    if active_start is not None:
        start_seconds = float(
            active_start["elapsed_seconds"]
        )
        end_seconds = max(
            start_seconds,
            float(duration_seconds),
        )

        board_splits.append(
            {
                "board": active_start["board"],
                "screen_name": active_start["screen_name"],
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "duration_seconds": (
                    end_seconds - start_seconds
                ),
                "score_start": int(active_start["score"]),
                "score_end": None,
                "score_gained": None,
                "completed": False,
            }
        )

    return board_splits


def build_session_detail(session_directory: Path) -> dict[str, Any]:
    """
    Build a dashboard-friendly summary for one tracked session.
    """
    event_rows = read_csv_rows(session_directory / "events.csv")
    score_rows = read_csv_rows(session_directory / "score_log.csv")

    score_points: list[dict[str, float | int]] = []

    for row in score_rows:
        score_points.append(
            {
                "elapsed_seconds": parse_float(
                    row.get("elapsed_seconds")
                ),
                "score": parse_int(
                    row.get("score")
                ),
            }
        )

    events: list[dict[str, Any]] = []

    highest_level = 0
    highest_board_position = 0
    lives_lost = 0
    bonus_lives = 0
    boards_cleared = 0

    for row in event_rows:
        event_name = row.get("event", "")
        level = parse_int(row.get("level"))
        board_position = parse_int(
            row.get("board_position")
        )

        if (level, board_position) > (
            highest_level,
            highest_board_position,
        ):
            highest_level = level
            highest_board_position = board_position

        if event_name == "life_lost":
            lives_lost += 1
        elif event_name == "bonus_life":
            bonus_lives += 1
        elif event_name == "level_transition":
            boards_cleared += 1

        events.append(
            {
                "elapsed_seconds": parse_float(
                    row.get("elapsed_seconds")
                ),
                "event": event_name,
                "score": parse_int(row.get("score")),
                "level": level,
                "board_position": board_position,
                "board": format_board(
                    level,
                    board_position,
                ),
                "screen_name": row.get(
                    "screen_name",
                    "",
                ),
                "lives": parse_int(
                    row.get("lives")
                ),
                "details": row.get("details", ""),
            }
        )

    final_score = (
        score_points[-1]["score"]
        if score_points
        else 0
    )

    duration_candidates = [
        point["elapsed_seconds"]
        for point in score_points
    ]
    duration_candidates.extend(
        event["elapsed_seconds"]
        for event in events
    )

    duration_seconds = max(
        duration_candidates,
        default=0.0,
    )

    board_splits = build_board_splits(
        events,
        duration_seconds,
    )

    return {
        "session_directory": str(session_directory),
        "final_score": final_score,
        "duration_seconds": duration_seconds,
        "highest_board": format_board(
            highest_level,
            highest_board_position,
        ),
        "lives_lost": lives_lost,
        "bonus_lives": bonus_lives,
        "boards_cleared": boards_cleared,
        "score_points": score_points,
        "events": events,
        "board_splits": board_splits,
    }