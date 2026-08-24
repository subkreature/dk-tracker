import csv
from pathlib import Path

from tracker.models import (
    Career,
    FailedSession,
    GameEvent,
    ScoreSample,
    Session,
)


LEGACY_EXCLUSION_MARKER_NAME = ".exclude-from-career"
GAME_EXCLUSIONS_FOLDER_NAME = ".excluded-games"


def read_csv_rows(
    csv_path: Path,
) -> list[dict[str, str]]:
    try:
        with csv_path.open(
            mode="r",
            encoding="utf-8",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            if reader.fieldnames is None:
                raise ValueError(
                    f"CSV file has no header:\n{csv_path}"
                )

            return list(reader)

    except csv.Error as error:
        raise ValueError(
            f"Could not read CSV file:\n"
            f"{csv_path}\n"
            f"{error}"
        ) from error


def parse_float(
    row: dict[str, str],
    field_name: str,
    csv_path: Path,
    row_number: int,
) -> float:
    raw_value = row.get(field_name)

    if raw_value is None or raw_value == "":
        raise ValueError(
            f"Missing value for '{field_name}' in:\n"
            f"{csv_path}\n"
            f"Data row: {row_number}"
        )

    try:
        return float(raw_value)

    except ValueError as error:
        raise ValueError(
            f"Invalid number for '{field_name}' in:\n"
            f"{csv_path}\n"
            f"Data row: {row_number}\n"
            f"Value: {raw_value!r}"
        ) from error


def parse_int(
    row: dict[str, str],
    field_name: str,
    csv_path: Path,
    row_number: int,
) -> int:
    raw_value = row.get(field_name)

    if raw_value is None or raw_value == "":
        raise ValueError(
            f"Missing value for '{field_name}' in:\n"
            f"{csv_path}\n"
            f"Data row: {row_number}"
        )

    try:
        return int(raw_value)

    except ValueError as error:
        raise ValueError(
            f"Invalid integer for '{field_name}' in:\n"
            f"{csv_path}\n"
            f"Data row: {row_number}\n"
            f"Value: {raw_value!r}"
        ) from error


def parse_score_samples(
    rows: list[dict[str, str]],
    csv_path: Path,
) -> list[ScoreSample]:
    score_samples: list[ScoreSample] = []

    for row_number, row in enumerate(
        rows,
        start=2,
    ):
        score_samples.append(
            ScoreSample(
                elapsed_seconds=parse_float(
                    row,
                    "elapsed_seconds",
                    csv_path,
                    row_number,
                ),
                score=parse_int(
                    row,
                    "score",
                    csv_path,
                    row_number,
                ),
            )
        )

    return score_samples


def parse_events(
    rows: list[dict[str, str]],
    csv_path: Path,
) -> list[GameEvent]:
    events: list[GameEvent] = []

    for row_number, row in enumerate(
        rows,
        start=2,
    ):
        event_name = row.get(
            "event",
            "",
        ).strip()

        screen_name = row.get(
            "screen_name",
            "",
        ).strip()

        details = row.get(
            "details",
            "",
        ).strip()

        if not event_name:
            raise ValueError(
                f"Missing value for 'event' in:\n"
                f"{csv_path}\n"
                f"Data row: {row_number}"
            )

        events.append(
            GameEvent(
                elapsed_seconds=parse_float(
                    row,
                    "elapsed_seconds",
                    csv_path,
                    row_number,
                ),
                event=event_name,
                score=parse_int(
                    row,
                    "score",
                    csv_path,
                    row_number,
                ),
                level=parse_int(
                    row,
                    "level",
                    csv_path,
                    row_number,
                ),
                board_position=parse_int(
                    row,
                    "board_position",
                    csv_path,
                    row_number,
                ),
                screen_type=parse_int(
                    row,
                    "screen_type",
                    csv_path,
                    row_number,
                ),
                screen_name=screen_name or "unknown",
                lives=parse_int(
                    row,
                    "lives",
                    csv_path,
                    row_number,
                ),
                details=details,
            )
        )

    return events


def load_session(
    session_path: Path,
) -> Session:
    if not session_path.exists():
        raise FileNotFoundError(
            f"Session folder not found:\n{session_path}"
        )

    if not session_path.is_dir():
        raise NotADirectoryError(
            f"Session path is not a folder:\n"
            f"{session_path}"
        )

    score_log = session_path / "score_log.csv"
    events_log = session_path / "events.csv"

    if not score_log.exists():
        raise FileNotFoundError(
            f"Missing file:\n{score_log}"
        )

    if not events_log.exists():
        raise FileNotFoundError(
            f"Missing file:\n{events_log}"
        )

    score_rows = read_csv_rows(score_log)
    event_rows = read_csv_rows(events_log)

    return Session(
        session_id=session_path.name,
        folder=session_path,
        score_log=score_log,
        events_log=events_log,
        score_samples=parse_score_samples(
            score_rows,
            score_log,
        ),
        events=parse_events(
            event_rows,
            events_log,
        ),
    )


def split_session_into_games(
    session: Session,
) -> list[Session]:
    """
    Split one legacy MAME-launch session into individual games.

    Each game begins with a game_start event and ends before
    the next game_start event. Elapsed times are rebased so
    each returned session begins at zero.
    """

    game_starts = [
        event
        for event in session.events
        if event.event == "game_start"
    ]

    games: list[Session] = []

    for index, game_start in enumerate(
        game_starts
    ):
        start_time = game_start.elapsed_seconds

        if index + 1 < len(game_starts):
            end_time = (
                game_starts[index + 1]
                .elapsed_seconds
            )
        else:
            end_time = None

        game_score_samples = [
            ScoreSample(
                elapsed_seconds=(
                    sample.elapsed_seconds
                    - start_time
                ),
                score=sample.score,
            )
            for sample in session.score_samples
            if sample.elapsed_seconds >= start_time
            and (
                end_time is None
                or sample.elapsed_seconds < end_time
            )
        ]

        game_events = [
            GameEvent(
                elapsed_seconds=(
                    event.elapsed_seconds
                    - start_time
                ),
                event=event.event,
                score=event.score,
                level=event.level,
                board_position=event.board_position,
                screen_type=event.screen_type,
                screen_name=event.screen_name,
                lives=event.lives,
                details=event.details,
            )
            for event in session.events
            if event.elapsed_seconds >= start_time
            and (
                end_time is None
                or event.elapsed_seconds < end_time
            )
        ]

        has_activity_after_start = (
            any(
                sample.elapsed_seconds > 0
                for sample in game_score_samples
            )
            or any(
                event.elapsed_seconds > 0
                for event in game_events
            )
        )

        if not has_activity_after_start:
            continue

        games.append(
            Session(
                session_id=(
                    f"{session.session_id}_"
                    f"{index + 1:02d}"
                ),
                folder=session.folder,
                score_log=session.score_log,
                events_log=session.events_log,
                score_samples=game_score_samples,
                events=game_events,
            )
        )

    return games


def get_game_exclusion_marker(
    session: Session,
) -> Path:
    """
    Return the exclusion marker path for one logical game.

    Logical games share a physical MAME-launch folder, so
    their exclusion markers live in a hidden subfolder inside
    that launch folder and are named with the full session ID.
    """

    return (
        session.folder
        / GAME_EXCLUSIONS_FOLDER_NAME
        / session.session_id
    )


def is_game_excluded(
    session: Session,
) -> bool:
    """
    Return whether one logical game is excluded from career
    analytics.
    """

    return get_game_exclusion_marker(
        session
    ).is_file()


def get_launch_folder_for_session_id(
    career_path: Path,
    session_id: str,
) -> Path:
    """
    Return the physical launch folder for one logical game ID.

    Logical IDs use the form:
    YYYY-MM-DD_HH-MM-SS_NN
    """

    if Path(session_id).name != session_id:
        raise ValueError(
            "The session ID is invalid."
        )

    parts = session_id.rsplit(
        "_",
        maxsplit=1,
    )

    if (
        len(parts) != 2
        or not parts[0]
        or not parts[1].isdigit()
        or int(parts[1]) <= 0
    ):
        raise ValueError(
            "The session ID is invalid."
        )

    return career_path / parts[0]


def load_game_session_by_id(
    career_path: Path,
    session_id: str,
) -> Session:
    """
    Load one logical game by session ID.

    This intentionally ignores per-game exclusion state so an
    excluded game can still be resolved and re-included.
    """

    launch_folder = (
        get_launch_folder_for_session_id(
            career_path,
            session_id,
        )
    )

    launch_session = load_session(
        launch_folder
    )

    for game_session in split_session_into_games(
        launch_session
    ):
        if game_session.session_id == session_id:
            return game_session

    raise ValueError(
        "The requested logical session does not exist."
    )


def set_game_excluded(
    career_path: Path,
    session_id: str,
    excluded: bool,
) -> Path:
    """
    Set one logical game's career-exclusion state.

    Raw telemetry is never changed. Exclusion is represented
    only by a marker file under .excluded-games.
    """

    session = load_game_session_by_id(
        career_path,
        session_id,
    )

    marker = get_game_exclusion_marker(
        session
    )

    if excluded:
        marker.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        marker.touch(
            exist_ok=True
        )
    else:
        if marker.is_file():
            marker.unlink()

        try:
            marker.parent.rmdir()
        except OSError:
            pass

    return marker


def load_excluded_game_sessions(
    career_path: Path,
) -> list[Session]:
    """
    Load logical games that are individually excluded.

    Legacy whole-launch exclusions are intentionally not
    expanded here. This helper is only for the new per-game
    exclusion system used by the History UI.
    """

    excluded_sessions: list[Session] = []

    for launch_folder in find_session_folders(
        career_path
    ):
        exclusion_folder = (
            launch_folder
            / GAME_EXCLUSIONS_FOLDER_NAME
        )

        if not exclusion_folder.is_dir():
            continue

        try:
            marker_files = sorted(
                marker
                for marker in exclusion_folder.iterdir()
                if marker.is_file()
            )
        except OSError:
            continue

        for marker in marker_files:
            try:
                session = load_game_session_by_id(
                    career_path,
                    marker.name,
                )
            except (
                FileNotFoundError,
                NotADirectoryError,
                OSError,
                ValueError,
            ):
                continue

            if is_game_excluded(session):
                excluded_sessions.append(
                    session
                )

    return sorted(
        excluded_sessions,
        key=lambda session: session.session_id,
        reverse=True,
    )


def find_session_folders(
    career_path: Path,
) -> list[Path]:
    if not career_path.exists():
        raise FileNotFoundError(
            f"Career folder not found:\n{career_path}"
        )

    if not career_path.is_dir():
        raise NotADirectoryError(
            f"Career path is not a folder:\n"
            f"{career_path}"
        )

    return sorted(
        folder
        for folder in career_path.iterdir()
        if folder.is_dir()
        and not folder.name.startswith(".")
    )


def load_career(
    career_path: Path,
) -> Career:
    session_folders = find_session_folders(
        career_path
    )

    sessions: list[Session] = []
    failed_sessions: list[FailedSession] = []
    excluded_sessions: list[Path] = []

    for session_folder in session_folders:
        exclusion_marker = (
            session_folder / LEGACY_EXCLUSION_MARKER_NAME
        )

        if exclusion_marker.is_file():
            excluded_sessions.append(
                session_folder
            )
            continue

        try:
            sessions.append(
                load_session(session_folder)
            )

        except (
            FileNotFoundError,
            NotADirectoryError,
            OSError,
            ValueError,
        ) as error:
            failed_sessions.append(
                FailedSession(
                    folder=session_folder,
                    reason=str(error),
                )
            )

    return Career(
        folder=career_path,
        sessions=sessions,
        failed_sessions=failed_sessions,
        excluded_sessions=excluded_sessions,
    )


def load_game_career(
    career_path: Path,
) -> Career:
    """
    Load career data using one credit/game as one Session.

    Physical folders still represent MAME launches. Each
    compatible launch is split at game_start boundaries into
    independent logical sessions.

    Existing launch-level exclusion markers remain supported:
    if a launch folder contains .exclude-from-career, none of
    its games are included.

    Individual logical games can also be excluded with marker
    files stored under .excluded-games inside the launch
    folder. Each marker is named with the full logical
    session ID.

    A launch that parses successfully but contains no
    game_start events is treated as incompatible rather than
    silently reintroducing the old one-launch-one-session
    behavior.
    """

    session_folders = find_session_folders(
        career_path
    )

    sessions: list[Session] = []
    failed_sessions: list[FailedSession] = []
    excluded_sessions: list[Path] = []

    for session_folder in session_folders:
        exclusion_marker = (
            session_folder / LEGACY_EXCLUSION_MARKER_NAME
        )

        if exclusion_marker.is_file():
            excluded_sessions.append(
                session_folder
            )
            continue

        try:
            launch_session = load_session(
                session_folder
            )

            game_sessions = (
                split_session_into_games(
                    launch_session
                )
            )

            if not game_sessions:
                failed_sessions.append(
                    FailedSession(
                        folder=session_folder,
                        reason=(
                            "No game_start events were "
                            "found in this launch."
                        ),
                    )
                )
                continue

            for game_session in game_sessions:
                if is_game_excluded(
                    game_session
                ):
                    excluded_sessions.append(
                        get_game_exclusion_marker(
                            game_session
                        )
                    )
                    continue

                sessions.append(
                    game_session
                )

        except (
            FileNotFoundError,
            NotADirectoryError,
            OSError,
            ValueError,
        ) as error:
            failed_sessions.append(
                FailedSession(
                    folder=session_folder,
                    reason=str(error),
                )
            )

    return Career(
        folder=career_path,
        sessions=sessions,
        failed_sessions=failed_sessions,
        excluded_sessions=excluded_sessions,
    )

