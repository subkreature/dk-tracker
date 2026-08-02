from statistics import mean, median

from tracker.models import (
    BoardPerformance,
    Career,
    CareerBoardStats,
    CareerSummary,
    GameEvent,
    Session,
    SessionSummary,
)


def find_events(
    session: Session,
    event_name: str,
) -> list[GameEvent]:
    return [
        event
        for event in session.events
        if event.event == event_name
    ]


def board_sort_key(
    event: GameEvent,
) -> tuple[int, int]:
    return (
        event.level,
        event.board_position,
    )


def get_final_score(
    session: Session,
) -> int:
    if not session.score_samples:
        return 0

    return session.score_samples[-1].score


def get_session_duration(
    session: Session,
) -> float:
    if session.score_samples:
        score_duration = (
            session.score_samples[-1]
            .elapsed_seconds
        )
    else:
        score_duration = 0.0

    if session.events:
        event_duration = max(
            event.elapsed_seconds
            for event in session.events
        )
    else:
        event_duration = 0.0

    return max(
        score_duration,
        event_duration,
    )


def analyze_board_performances(
    session: Session,
    final_score: int,
) -> list[BoardPerformance]:
    board_start_events = find_events(
        session,
        "board_start",
    )

    board_clear_events = find_events(
        session,
        "level_transition",
    )

    life_lost_events = find_events(
        session,
        "life_lost",
    )

    if not board_start_events:
        return []

    first_board_starts: dict[
        tuple[int, int],
        GameEvent,
    ] = {}

    ordered_board_keys: list[
        tuple[int, int]
    ] = []

    for event in board_start_events:
        board_key = event.board_key

        if board_key in first_board_starts:
            continue

        first_board_starts[board_key] = event
        ordered_board_keys.append(board_key)

    clear_events_by_board: dict[
        tuple[int, int],
        GameEvent,
    ] = {}

    for event in board_clear_events:
        board_key = event.board_key

        if board_key not in clear_events_by_board:
            clear_events_by_board[board_key] = event

    deaths_by_board: dict[
        tuple[int, int],
        int,
    ] = {}

    for event in life_lost_events:
        board_key = event.board_key

        deaths_by_board[board_key] = (
            deaths_by_board.get(
                board_key,
                0,
            )
            + 1
        )

    board_performances: list[
        BoardPerformance
    ] = []

    for index, board_key in enumerate(
        ordered_board_keys
    ):
        board_start = first_board_starts[
            board_key
        ]

        clear_event = clear_events_by_board.get(
            board_key
        )

        if clear_event is not None:
            end_score = clear_event.score
            cleared = True

        elif index + 1 < len(ordered_board_keys):
            next_board_key = ordered_board_keys[
                index + 1
            ]

            next_board_start = first_board_starts[
                next_board_key
            ]

            end_score = next_board_start.score
            cleared = False

        else:
            end_score = final_score
            cleared = False

        points_gained = (
            end_score
            - board_start.score
        )

        board_performances.append(
            BoardPerformance(
                level=board_start.level,
                board_position=(
                    board_start.board_position
                ),
                screen_name=(
                    board_start.screen_name
                ),
                start_score=board_start.score,
                end_score=end_score,
                points_gained=points_gained,
                deaths=deaths_by_board.get(
                    board_key,
                    0,
                ),
                cleared=cleared,
            )
        )

    return board_performances


def analyze_session(
    session: Session,
) -> SessionSummary:
    final_score = get_final_score(
        session
    )

    duration_seconds = get_session_duration(
        session
    )

    life_lost_events = find_events(
        session,
        "life_lost",
    )

    board_clear_events = find_events(
        session,
        "level_transition",
    )

    board_start_events = find_events(
        session,
        "board_start",
    )

    game_over = bool(
        find_events(
            session,
            "game_over",
        )
    )

    first_death_score: int | None = None

    if life_lost_events:
        first_death_score = (
            life_lost_events[0].score
        )

    starting_board: str | None = None
    ending_board: str | None = None
    furthest_board: str | None = None

    if board_start_events:
        starting_board = (
            board_start_events[0].board_label
        )

        ending_board = (
            board_start_events[-1].board_label
        )

        furthest_event = max(
            board_start_events,
            key=board_sort_key,
        )

        furthest_board = (
            furthest_event.board_label
        )

    board_performances = (
        analyze_board_performances(
            session,
            final_score,
        )
    )

    return SessionSummary(
        final_score=final_score,
        duration_seconds=duration_seconds,
        lives_lost=len(life_lost_events),
        boards_cleared=len(
            board_clear_events
        ),
        game_over=game_over,
        first_death_score=first_death_score,
        starting_board=starting_board,
        ending_board=ending_board,
        furthest_board=furthest_board,
        board_performances=board_performances,
    )


def analyze_career_board_stats(
    session_summaries: list[SessionSummary],
) -> list[CareerBoardStats]:
    performances_by_board: dict[
        tuple[int, int],
        list[BoardPerformance],
    ] = {}

    for summary in session_summaries:
        for performance in summary.board_performances:
            performances_by_board.setdefault(
                performance.board_key,
                [],
            ).append(performance)

    board_stats: list[CareerBoardStats] = []

    for board_key in sorted(
        performances_by_board
    ):
        performances = performances_by_board[
            board_key
        ]

        first_performance = performances[0]

        points_gained_values = [
            performance.points_gained
            for performance in performances
        ]

        board_stats.append(
            CareerBoardStats(
                level=first_performance.level,
                board_position=(
                    first_performance.board_position
                ),
                screen_name=(
                    first_performance.screen_name
                ),
                attempts=len(performances),
                clears=sum(
                    1
                    for performance in performances
                    if performance.cleared
                ),
                deaths=sum(
                    performance.deaths
                    for performance in performances
                ),
                average_points_gained=mean(
                    points_gained_values
                ),
                best_points_gained=max(
                    points_gained_values
                ),
            )
        )

    return board_stats


def analyze_career(
    career: Career,
) -> CareerSummary:
    session_summaries = [
        analyze_session(session)
        for session in career.sessions
    ]

    if not session_summaries:
        raise ValueError(
            "No compatible sessions were available "
            "for career analysis."
        )

    final_scores = [
        summary.final_score
        for summary in session_summaries
    ]

    first_death_scores = [
        summary.first_death_score
        for summary in session_summaries
        if summary.first_death_score is not None
    ]

    completed_games = sum(
        1
        for summary in session_summaries
        if summary.game_over
    )

    board_stats = analyze_career_board_stats(
        session_summaries
    )

    return CareerSummary(
        tracked_sessions=len(session_summaries),
        skipped_sessions=(
            len(career.failed_sessions)
            + len(career.excluded_sessions)
        ),
        high_score=max(final_scores),
        average_score=mean(final_scores),
        median_score=median(final_scores),
        lifetime_points=sum(final_scores),
        total_play_time_seconds=sum(
            summary.duration_seconds
            for summary in session_summaries
        ),
        total_boards_cleared=sum(
            summary.boards_cleared
            for summary in session_summaries
        ),
        total_lives_lost=sum(
            summary.lives_lost
            for summary in session_summaries
        ),
        completed_games=completed_games,
        quit_or_incomplete_games=(
            len(session_summaries)
            - completed_games
        ),
        average_first_death_score=(
            mean(first_death_scores)
            if first_death_scores
            else None
        ),
        board_stats=board_stats,
    )