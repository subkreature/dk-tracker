import csv
from pathlib import Path

from tracker.models import (
    Career,
    FailedSession,
    GameEvent,
    ScoreSample,
    Session,
)


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
            session_folder / ".exclude-from-career"
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