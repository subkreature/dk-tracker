from tracker.live import (
    count_live_events,
    get_lives_remaining,
    parse_nonnegative_int,
)


def test_parse_nonnegative_int() -> None:
    assert parse_nonnegative_int("3") == 3
    assert parse_nonnegative_int(0) == 0
    assert parse_nonnegative_int("-1") is None
    assert parse_nonnegative_int("not a number") is None
    assert parse_nonnegative_int(None) is None


def test_count_live_events() -> None:
    rows = [
        {"event": "life_lost"},
        {"event": "board_clear"},
        {"event": "life_lost"},
    ]

    assert count_live_events(rows, "life_lost") == 2
    assert count_live_events(rows, "board_clear") == 1
    assert count_live_events(rows, "bonus_life") == 0


def test_get_lives_remaining() -> None:
    rows = [
        {"event": "game_start", "lives": "3"},
        {"event": "life_lost", "lives": "2"},
    ]

    assert get_lives_remaining(rows) == 2