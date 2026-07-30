#!/usr/bin/env python3

import argparse
import csv
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tracker.config import (
    load_config,
    validate_config,
)


# ---------------------------------------------------------
# Project configuration
# ---------------------------------------------------------

PROJECT_FOLDER = Path(__file__).resolve().parent
DATA_FOLDER = PROJECT_FOLDER / "data"
SESSIONS_FOLDER = DATA_FOLDER / "sessions"
SESSION_HISTORY_FILE = DATA_FOLDER / "sessions.csv"

SAVED_CONFIG = load_config()

MAME_EXECUTABLE = Path(
    SAVED_CONFIG.mame_executable
)

MAME_FOLDER = MAME_EXECUTABLE.parent

ROM_FILE = Path(
    SAVED_CONFIG.rom_file
)

ROM_FOLDER = ROM_FILE.parent

ROM_NAME = "dkong"
PLUGIN_NAME = "dktracker"

PROJECT_PLUGIN = (
    PROJECT_FOLDER
    / "plugins"
    / PLUGIN_NAME
    / "init.lua"
)

MAME_PLUGIN = (
    MAME_FOLDER
    / "plugins"
    / PLUGIN_NAME
    / "init.lua"
)


# ---------------------------------------------------------
# Models
# ---------------------------------------------------------

@dataclass(frozen=True)
class LaunchResult:
    tracking_enabled: bool
    return_code: int
    session_folder: Path | None = None
    final_score: int | None = None
    lives_lost: int | None = None
    bonus_lives: int | None = None
    boards_cleared: int | None = None
    game_over: bool | None = None
    starting_board: str | None = None
    ending_board: str | None = None
    furthest_board: str | None = None


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def format_bytes(size_bytes: int) -> str:
    """Return a human-readable storage size."""

    size = float(size_bytes)

    for unit in ("bytes", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "bytes":
                return f"{int(size)} {unit}"

            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{size_bytes} bytes"


def get_folder_size(folder: Path) -> int:
    """Return the total size of all files inside a folder."""

    if not folder.exists():
        return 0

    total_size = 0

    for path in folder.rglob("*"):
        if not path.is_file():
            continue

        try:
            total_size += path.stat().st_size
        except OSError:
            pass

    return total_size


def read_csv_rows(
    csv_file: Path,
) -> list[dict[str, str]]:
    """Read a CSV file into a list of dictionaries."""

    if not csv_file.exists():
        return []

    try:
        with csv_file.open(
            "r",
            newline="",
            encoding="utf-8",
        ) as file:
            return list(csv.DictReader(file))

    except (OSError, csv.Error):
        return []


def get_final_score(
    score_rows: list[dict[str, str]],
) -> int:
    """Return the highest valid score in the session."""

    scores: list[int] = []

    for row in score_rows:
        try:
            scores.append(int(row["score"]))
        except (KeyError, TypeError, ValueError):
            continue

    return max(scores, default=0)


def count_events(
    event_rows: list[dict[str, str]],
    event_name: str,
) -> int:
    """Count events matching the requested name."""

    return sum(
        1
        for row in event_rows
        if row.get("event") == event_name
    )


def has_event(
    event_rows: list[dict[str, str]],
    event_name: str,
) -> bool:
    """Return whether an event occurred at least once."""

    return any(
        row.get("event") == event_name
        for row in event_rows
    )


def parse_positive_int(
    value: str | None,
) -> int | None:
    """Convert a CSV value to a positive integer."""

    if value is None:
        return None

    try:
        number = int(value)
    except (TypeError, ValueError):
        return None

    if number <= 0:
        return None

    return number


def get_board_label(
    level: int,
    board_position: int,
    screen_name: str,
) -> str:
    """Return a player-facing board label."""

    cleaned_name = (
        screen_name.strip().replace("_", " ")
    )

    if cleaned_name and cleaned_name != "unknown":
        return (
            f"{level}-{board_position} "
            f"({cleaned_name})"
        )

    return f"{level}-{board_position}"


def get_board_summary(
    event_rows: list[dict[str, str]],
) -> tuple[str, str, str]:
    """Return starting, ending, and furthest board reached."""

    boards: list[dict[str, object]] = []

    for row in event_rows:
        if row.get("event") != "board_start":
            continue

        level = parse_positive_int(
            row.get("level")
        )

        board_position = parse_positive_int(
            row.get("board_position")
        )

        if level is None or board_position is None:
            continue

        name = row.get(
            "screen_name",
            "unknown",
        )

        boards.append(
            {
                "level": level,
                "board_position": board_position,
                "label": get_board_label(
                    level,
                    board_position,
                    name,
                ),
            }
        )

    if not boards:
        return "Unknown", "Unknown", "Unknown"

    starting_board = str(boards[0]["label"])
    ending_board = str(boards[-1]["label"])

    furthest = max(
        boards,
        key=lambda board: (
            int(board["level"]),
            int(board["board_position"]),
        ),
    )

    furthest_board = str(furthest["label"])

    return (
        starting_board,
        ending_board,
        furthest_board,
    )


def validate_mame() -> None:
    """
    Confirm that the saved MAME and ROM configuration is valid.
    """

    problems = validate_config(
        SAVED_CONFIG
    )

    if problems:
        details = "\n".join(
            f"- {problem}"
            for problem in problems
        )

        raise FileNotFoundError(
            "DK Tracker setup is incomplete:\n"
            f"{details}"
        )


def prepare_data_folders() -> None:
    """Create tracker data directories when needed."""

    DATA_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    SESSIONS_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )


def print_tracker_storage() -> None:
    """Print current tracked-session storage information."""

    existing_sessions = [
        path
        for path in SESSIONS_FOLDER.iterdir()
        if path.is_dir()
    ]

    existing_storage = get_folder_size(
        SESSIONS_FOLDER
    )

    print("Tracker storage:")
    print(
        f"  Existing sessions: "
        f"{len(existing_sessions)}"
    )
    print(
        f"  Disk usage: "
        f"{format_bytes(existing_storage)}"
    )
    print()



def sync_plugin() -> None:
    """Copy the latest tracker plugin into the MAME plugins folder."""

    if not PROJECT_PLUGIN.exists():
        raise FileNotFoundError(
            "Tracker plugin not found:\n"
            f"{PROJECT_PLUGIN}"
        )

    mame_plugin = (
        MAME_FOLDER
        / "plugins"
        / PLUGIN_NAME
        / "init.lua"
    )

    mame_plugin.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if (
        PROJECT_PLUGIN.resolve()
        == mame_plugin.resolve()
    ):
        print(
            "Tracker plugin is already "
            "in the MAME plugins folder."
        )
        return

    shutil.copy2(
        PROJECT_PLUGIN,
        mame_plugin,
    )

    print("Tracker plugin synchronized.")

def build_mame_command(
    tracking_enabled: bool,
) -> list[str]:
    """Build the command used to launch Donkey Kong."""

    command = [
        str(MAME_EXECUTABLE),
        ROM_NAME,
        "-rompath",
        str(ROM_FOLDER),
    ]

    if tracking_enabled:
        command.extend(
            [
                "-plugin",
                PLUGIN_NAME,
            ]
        )
    else:
        command.extend(
            [
                "-noplugin",
                PLUGIN_NAME,
            ]
        )

    return command


def run_mame(
    tracking_enabled: bool,
) -> int:
    """Launch MAME and return its exit code."""

    command = build_mame_command(
        tracking_enabled
    )

    return subprocess.run(
        command,
        cwd=MAME_FOLDER,
        check=False,
    ).returncode


def append_session_history(
    session_name: str,
    start_time: datetime,
    end_time: datetime,
    duration_seconds: float,
    final_score: int,
    lives_lost: int,
    bonus_lives: int,
    boards_cleared: int,
    starting_board: str,
    ending_board: str,
    furthest_board: str,
    session_size: int,
    return_code: int,
    session_folder: Path,
) -> None:
    """Append one tracked session to the persistent history CSV."""

    history_exists = (
        SESSION_HISTORY_FILE.exists()
    )

    history_is_empty = (
        not history_exists
        or SESSION_HISTORY_FILE.stat().st_size == 0
    )

    with SESSION_HISTORY_FILE.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        if history_is_empty:
            writer.writerow(
                [
                    "session_id",
                    "start_time",
                    "end_time",
                    "duration_seconds",
                    "final_score",
                    "lives_lost",
                    "bonus_lives",
                    "boards_cleared",
                    "starting_board",
                    "ending_board",
                    "furthest_board",
                    "session_size_bytes",
                    "mame_exit_code",
                    "session_folder",
                ]
            )

        writer.writerow(
            [
                session_name,
                start_time.isoformat(),
                end_time.isoformat(),
                round(duration_seconds, 3),
                final_score,
                lives_lost,
                bonus_lives,
                boards_cleared,
                starting_board,
                ending_board,
                furthest_board,
                session_size,
                return_code,
                str(session_folder.resolve()),
            ]
        )


# ---------------------------------------------------------
# Launch modes
# ---------------------------------------------------------

def launch_untracked_game() -> LaunchResult:
    """Launch Donkey Kong without creating tracker data."""

    print("===================================")
    print("        DK Tracker")
    print("===================================")
    print()
    print("UNTRACKED PLAY")
    print("No session statistics will be saved.")
    print()

    start_time = datetime.now()

    return_code = run_mame(
        tracking_enabled=False
    )

    end_time = datetime.now()
    duration = end_time - start_time

    print()
    print("Game finished!")
    print(f"Ended: {end_time}")
    print(f"Duration: {duration}")
    print(f"MAME exit code: {return_code}")
    print()
    print("No tracker session was created.")

    return LaunchResult(
        tracking_enabled=False,
        return_code=return_code,
    )


def launch_tracked_game() -> LaunchResult:
    """Launch Donkey Kong with telemetry and save a session."""

    print("===================================")
    print("        DK Tracker")
    print("===================================")
    print()

    prepare_data_folders()
    sync_plugin()
    print_tracker_storage()

    start_time = datetime.now()

    session_name = start_time.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    session_folder = (
        SESSIONS_FOLDER / session_name
    )

    session_folder.mkdir(
        parents=True,
        exist_ok=False,
    )

    score_file = (
        session_folder / "score_log.csv"
    )

    event_file = (
        session_folder / "events.csv"
    )

    print("TRACKING ACTIVE")
    print(f"Session started: {start_time}")
    print(f"Session folder: {session_folder}")
    print()

    score_path_file = (
        MAME_FOLDER / "score_path.txt"
    )

    events_path_file = (
        MAME_FOLDER / "events_path.txt"
    )

    score_path_file.write_text(
        str(score_file.resolve()),
        encoding="utf-8",
    )

    events_path_file.write_text(
        str(event_file.resolve()),
        encoding="utf-8",
    )

    return_code = run_mame(
        tracking_enabled=True
    )

    end_time = datetime.now()
    duration = end_time - start_time
    duration_seconds = duration.total_seconds()

    score_rows = read_csv_rows(score_file)
    event_rows = read_csv_rows(event_file)

    final_score = get_final_score(score_rows)

    lives_lost = count_events(
        event_rows,
        "life_lost",
    )

    boards_cleared = count_events(
        event_rows,
        "level_transition",
    )

    bonus_lives = count_events(
        event_rows,
        "bonus_life",
    )

    game_over = has_event(
        event_rows,
        "game_over",
    )

    (
        starting_board,
        ending_board,
        furthest_board,
    ) = get_board_summary(event_rows)

    session_size = get_folder_size(
        session_folder
    )

    print()
    print("Game finished!")
    print(f"Ended: {end_time}")
    print(f"Duration: {duration}")
    print()

    print("===================================")
    print("        Session Summary")
    print("===================================")
    print(f"Final score: {final_score}")
    print(f"Lives lost: {lives_lost}")
    print(f"Bonus lives: {bonus_lives}")
    print(f"Boards cleared: {boards_cleared}")
    print(f"Game over: {'Yes' if game_over else 'No'}")
    print(f"Starting board: {starting_board}")
    print(f"Ending board: {ending_board}")
    print(f"Furthest board: {furthest_board}")
    print(
        f"Session storage: "
        f"{format_bytes(session_size)}"
    )
    print(f"MAME exit code: {return_code}")
    print()
    print("Files written:")
    print(f"  {score_file}")
    print(f"  {event_file}")
    print("===================================")

    append_session_history(
        session_name=session_name,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration_seconds,
        final_score=final_score,
        lives_lost=lives_lost,
        bonus_lives=bonus_lives,
        boards_cleared=boards_cleared,
        starting_board=starting_board,
        ending_board=ending_board,
        furthest_board=furthest_board,
        session_size=session_size,
        return_code=return_code,
        session_folder=session_folder,
    )

    total_sessions = len(
        [
            path
            for path in SESSIONS_FOLDER.iterdir()
            if path.is_dir()
        ]
    )

    total_storage = get_folder_size(
        SESSIONS_FOLDER
    )

    print()
    print("Session saved.")
    print(
        f"Total tracked sessions: "
        f"{total_sessions}"
    )
    print(
        f"Total tracker storage: "
        f"{format_bytes(total_storage)}"
    )

    return LaunchResult(
        tracking_enabled=True,
        return_code=return_code,
        session_folder=session_folder,
        final_score=final_score,
        lives_lost=lives_lost,
        bonus_lives=bonus_lives,
        boards_cleared=boards_cleared,
        game_over=game_over,
        starting_board=starting_board,
        ending_board=ending_board,
        furthest_board=furthest_board,
    )


def launch_game(
    tracking_enabled: bool = True,
) -> LaunchResult:
    """
    Launch Donkey Kong in the requested mode.

    This is the function the dashboard will call.
    """
    global SAVED_CONFIG
    global MAME_EXECUTABLE
    global MAME_FOLDER
    global ROM_FILE
    global ROM_FOLDER

    SAVED_CONFIG = load_config()

    MAME_EXECUTABLE = Path(
        SAVED_CONFIG.mame_executable
    )

    MAME_FOLDER = MAME_EXECUTABLE.parent

    ROM_FILE = Path(
        SAVED_CONFIG.rom_file
    )

    ROM_FOLDER = ROM_FILE.parent
    validate_mame()

    if tracking_enabled:
        return launch_tracked_game()

    return launch_untracked_game()


# ---------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch Donkey Kong through DK Tracker."
    )

    parser.add_argument(
        "--no-tracking",
        action="store_true",
        help=(
            "Launch Donkey Kong without the DK Tracker "
            "plugin or session logging."
        ),
    )

    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    try:
        result = launch_game(
            tracking_enabled=not arguments.no_tracking
        )

    except (
        FileExistsError,
        FileNotFoundError,
        OSError,
    ) as error:
        print(error)
        return 1

    return result.return_code


if __name__ == "__main__":
    raise SystemExit(main())