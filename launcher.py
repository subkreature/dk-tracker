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


def read_score_log(score_file: Path) -> list[dict[str, str]]:
    """Read score telemetry from the session score file."""

    if not score_file.exists():
        return []

    try:
        with score_file.open("r", newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except (OSError, csv.Error):
        return []


def read_event_log(event_file: Path) -> list[dict[str, str]]:
    """Read semantic gameplay events from the session event file."""

    if not event_file.exists():
        return []

    try:
        with event_file.open("r", newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except (OSError, csv.Error):
        return []


def get_final_score(score_rows: list[dict[str, str]]) -> int:
    """Return the highest valid score recorded during the session."""

    scores = []

    for row in score_rows:
        try:
            scores.append(int(row["score"]))
        except (KeyError, TypeError, ValueError):
            continue

    return max(scores, default=0)


def count_events(
    event_rows: list[dict[str, str]],
    event_name: str
) -> int:
    """Count events matching a semantic event name."""

    return sum(
        1
        for row in event_rows
        if row.get("event") == event_name
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
        f"MAME executable was not found at:\n{MAME_EXECUTABLE}"
    )

DATA_FOLDER.mkdir(parents=True, exist_ok=True)
SESSIONS_FOLDER.mkdir(parents=True, exist_ok=True)

existing_sessions = [
    path
    for path in SESSIONS_FOLDER.iterdir()
    if path.is_dir()
]

existing_storage = get_folder_size(SESSIONS_FOLDER)

print("Tracker storage:")
print(f"  Existing sessions: {len(existing_sessions)}")
print(f"  Disk usage: {format_bytes(existing_storage)}")
print()

start_time = datetime.now()

session_name = start_time.strftime("%Y-%m-%d_%H-%M-%S")
session_folder = SESSIONS_FOLDER / session_name
session_folder.mkdir(parents=True, exist_ok=False)

score_file = session_folder / "score_log.csv"
event_file = session_folder / "events.csv"

print(f"Session started: {start_time}")
print(f"Session folder: {session_folder}")
print()

# MAME's Lua plugin reads these small path files to discover where
# the current session's telemetry should be written.

score_path_file = MAME_FOLDER / "score_path.txt"
events_path_file = MAME_FOLDER / "events_path.txt"

score_path_file.write_text(
    str(score_file.resolve()),
    encoding="utf-8"
)

events_path_file.write_text(
    str(event_file.resolve()),
    encoding="utf-8"
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

score_rows = read_score_log(score_file)
event_rows = read_event_log(event_file)

final_score = get_final_score(score_rows)
lives_lost = count_events(event_rows, "life_lost")
levels_cleared = count_events(event_rows, "level_transition")

session_size = get_folder_size(session_folder)

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
print(f"Levels cleared: {levels_cleared}")
print(f"Session storage: {format_bytes(session_size)}")
print(f"MAME exit code: {return_code}")
print()
print("Files written:")
print(f"  {score_file}")
print(f"  {event_file}")
print("===================================")


# ---------------------------------------------------------
# Append persistent session history
# ---------------------------------------------------------

history_exists = SESSION_HISTORY_FILE.exists()

with SESSION_HISTORY_FILE.open(
    "a",
    newline="",
    encoding="utf-8"
) as file:
    writer = csv.writer(file)

    if not history_exists:
        writer.writerow(
            [
                "session_id",
                "start_time",
                "end_time",
                "duration_seconds",
                "final_score",
                "lives_lost",
                "levels_cleared",
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
            levels_cleared,
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

total_storage = get_folder_size(SESSIONS_FOLDER)

print()
print("Session saved.")
print(f"Total tracked sessions: {total_sessions}")
print(f"Total tracker storage: {format_bytes(total_storage)}")