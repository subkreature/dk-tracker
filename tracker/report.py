from tracker.models import (
    BoardPerformance,
    Session,
    SessionSummary,
)


def format_duration(
    seconds: float,
) -> str:
    total_seconds = max(
        0,
        round(seconds),
    )

    minutes, remaining_seconds = divmod(
        total_seconds,
        60,
    )

    return (
        f"{minutes}m "
        f"{remaining_seconds:02d}s"
    )


def format_optional_score(
    score: int | None,
) -> str:
    if score is None:
        return "Not recorded"

    return f"{score:,}"


def format_optional_text(
    value: str | None,
) -> str:
    if value is None:
        return "Not recorded"

    return value


def print_board_performance(
    performance: BoardPerformance,
) -> None:
    print()
    print(performance.board_label)
    print(
        f"  Start score   : "
        f"{performance.start_score:,}"
    )
    print(
        f"  End score     : "
        f"{performance.end_score:,}"
    )
    print(
        f"  Points gained : "
        f"{performance.points_gained:,}"
    )
    print(
        f"  Deaths        : "
        f"{performance.deaths}"
    )
    print(
        f"  Cleared       : "
        f"{'Yes' if performance.cleared else 'No'}"
    )


def print_session_report(
    session: Session,
    summary: SessionSummary,
) -> None:
    print("===================================")
    print(" Donkey Kong Session Analyzer")
    print("===================================")
    print()

    print(
        f"Session          : "
        f"{session.folder.name}"
    )

    print(
        f"Score samples    : "
        f"{len(session.score_samples)}"
    )

    print(
        f"Events           : "
        f"{len(session.events)}"
    )

    print()
    print("-----------------------------------")
    print(" Session Summary")
    print("-----------------------------------")

    print(
        f"Final score      : "
        f"{summary.final_score:,}"
    )

    print(
        f"Duration         : "
        f"{format_duration(summary.duration_seconds)}"
    )

    print(
        f"Lives lost       : "
        f"{summary.lives_lost}"
    )

    print(
        f"Boards cleared   : "
        f"{summary.boards_cleared}"
    )

    print(
        f"Game over        : "
        f"{'Yes' if summary.game_over else 'No'}"
    )

    print(
        f"First death score: "
        f"{format_optional_score(summary.first_death_score)}"
    )

    print(
        f"Starting board   : "
        f"{format_optional_text(summary.starting_board)}"
    )

    print(
        f"Ending board     : "
        f"{format_optional_text(summary.ending_board)}"
    )

    print(
        f"Furthest board   : "
        f"{format_optional_text(summary.furthest_board)}"
    )

    print()
    print("-----------------------------------")
    print(" Board Performance")
    print("-----------------------------------")

    if summary.board_performances:
        for performance in summary.board_performances:
            print_board_performance(
                performance
            )
    else:
        print()
        print("No board data recorded.")

    print()
    print()
    print("Session analyzed successfully.")