def parse_nonnegative_int(
    value: object,
) -> int | None:
    """
    Parse a nonnegative integer safely.
    """

    try:
        parsed = int(str(value))
    except (
        TypeError,
        ValueError,
    ):
        return None

    if parsed < 0:
        return None

    return parsed


def count_live_events(
    event_rows: list[dict[str, str]],
    event_name: str,
) -> int:
    """
    Count matching telemetry events.
    """

    return sum(
        1
        for row in event_rows
        if row.get("event") == event_name
    )


def get_lives_remaining(
    event_rows: list[dict[str, str]],
) -> int | None:
    """
    Return the newest valid remaining-lives value.

    The Lua plugin writes the current lives value into every
    event row. Reading backward gives us the most recent
    complete value recorded during the active session.
    """

    for row in reversed(event_rows):
        lives = parse_nonnegative_int(
            row.get("lives")
        )

        if lives is not None:
            return lives

    return None