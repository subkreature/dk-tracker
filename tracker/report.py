from tracker.models import (
    BoardPerformance,
    Career,
    CareerSummary,
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


def format_long_duration(
    seconds: float,
) -> str:
    total_seconds = max(
        0,
        round(seconds),
    )

    hours, remainder = divmod(
        total_seconds,
        3600,
    )

    minutes, remaining_seconds = divmod(
        remainder,
        60,
    )

    return (
        f"{hours}h "
        f"{minutes:02d}m "
        f"{remaining_seconds:02d}s"
    )


def format_optional_score(
    score: int | None,
) -> str:
    if score is None:
        return "Not recorded"

    return f"{score:,}"


def format_optional_average(
    score: float | None,
) -> str:
    if score is None:
        return "Not enough data"

    return f"{score:,.0f}"


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


def print_career_report(
    career: Career,
    summary: CareerSummary,
) -> None:
    total_folders = (
        summary.tracked_sessions
        + summary.skipped_sessions
    )

    print("===================================")
    print(" Donkey Kong Career Analyzer")
    print("===================================")
    print()

    print(
        f"Career folder       : "
        f"{career.folder}"
    )

    print(
        f"Session folders found: "
        f"{total_folders}"
    )

    print(
        f"Compatible sessions : "
        f"{summary.tracked_sessions}"
    )

    print(
        f"Legacy sessions skipped: "
        f"{summary.skipped_sessions}"
    )

    print()
    print("-----------------------------------")
    print(" Career Summary")
    print("-----------------------------------")

    print(
        f"High score          : "
        f"{summary.high_score:,}"
    )

    print(
        f"Average score       : "
        f"{summary.average_score:,.0f}"
    )

    print(
        f"Median score        : "
        f"{summary.median_score:,.0f}"
    )

    print(
        f"Lifetime points     : "
        f"{summary.lifetime_points:,}"
    )

    print(
        f"Total play time     : "
        f"{format_long_duration(summary.total_play_time_seconds)}"
    )

    print(
        f"Boards cleared      : "
        f"{summary.total_boards_cleared}"
    )

    print(
        f"Lives lost          : "
        f"{summary.total_lives_lost}"
    )

    print(
        f"Game-over sessions  : "
        f"{summary.completed_games}"
    )

    print(
        f"Quit/incomplete     : "
        f"{summary.quit_or_incomplete_games}"
    )

    print(
        f"Average first death : "
        f"{format_optional_average(summary.average_first_death_score)}"
    )

    if career.failed_sessions:
        print()
        print("-----------------------------------")
        print(" Legacy Sessions Excluded")
        print("-----------------------------------")

        for failed_session in career.failed_sessions:
            print(
                f"  {failed_session.folder.name}"
            )

    print()
    print("Career analysis completed.")