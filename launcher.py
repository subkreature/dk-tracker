import csv
import subprocess
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------
# Project configuration
# ---------------------------------------------------------

PROJECT_FOLDER = Path(__file__).resolve().parent
DATA_FOLDER = PROJECT_FOLDER / "data"
SESSIONS_FOLDER = DATA_FOLDER / "sessions"
SESSION_HISTORY_FILE = DATA_FOLDER / "sessions.csv"

MAME_FOLDER = Path("/Users/nick/Downloads/mame0286-x86")
MAME_EXECUTABLE = MAME_FOLDER / "mame"

ROM_NAME = "dkong"
PLUGIN_NAME = "dktracker"


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
        if path.is_file():
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


# ---------------------------------------------------------
# Startup
# ---------------------------------------------------------

print("===================================")
print("        DK Tracker")
print("===================================")
print()

if not MAME_EXECUTABLE.exists():
    raise FileNotFoundError(
        f"MAME executable was not found at:\n"
        f"{MAME_EXECUTABLE}"
    )

DATA_FOLDER.mkdir(
    parents=True,
    exist_ok=True,
)

SESSIONS_FOLDER.mkdir(
    parents=True,
    exist_ok=True,
)

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


# ---------------------------------------------------------
# Launch MAME
# ---------------------------------------------------------

return_code = subprocess.run(
    [
        "./mame",
        ROM_NAME,
        "-plugin",
        PLUGIN_NAME,
    ],
    cwd=MAME_FOLDER,
    check=False,
).returncode


# ---------------------------------------------------------
# Build session summary
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Append persistent session history
#
# Keep the existing sessions.csv layout unchanged for now.
# Game-over status remains available in events.csv and can
# be added during the later database/dashboard migration.
# ---------------------------------------------------------

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