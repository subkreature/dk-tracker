from __future__ import annotations
from tracker.live import (
    count_live_events,
    get_lives_remaining,
)
from tracker.config import (
    DashboardSettings,
    SESSIONS_FOLDER,
    USER_DATA_FOLDER,
    load_config,
    load_dashboard_settings,
    save_dashboard_settings,
    validate_config,
)
from tracker.setup_page import (
    build_setup_page,
)
from tracker.support_page import (
    build_support_page,
)
from tracker.personal_best import (
    build_personal_bests,
)
from tracker.session_page import (
    build_session_page,
)
from tracker.session_detail import (
    build_session_detail_from_session,
)

import csv
from datetime import datetime
from html import escape
from http import HTTPStatus
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import webbrowser
from urllib.parse import parse_qs, urlparse

from launcher import (
    LaunchResult,
    launch_game,
)
from tracker.analyzer import (
    analyze_career,
    analyze_session,
)
from tracker.models import (
    CareerSummary,
    SessionSummary,
)
from tracker.parser import (
    load_excluded_game_sessions,
    load_game_career,
    set_game_excluded,
)


HOST = "127.0.0.1"
PORT = 5000

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHART_JS_FILE = (
    PROJECT_ROOT
    / "vendor"
    / "chartjs"
    / "chart.umd.min.js"
)


# ---------------------------------------------------------
# Launch state
# ---------------------------------------------------------

LAUNCH_LOCK = threading.Lock()

LAUNCH_STATE: dict[str, object] = {
    "state": "ready",
    "mode": None,
    "message": "Ready to play.",
    "started_at": None,
    "ended_at": None,
    "return_code": None,
    "session_folder": None,
    "final_score": None,
}


def get_launch_state() -> dict[str, object]:
    """
    Return a safe copy of the current launch state.
    """

    with LAUNCH_LOCK:
        return dict(LAUNCH_STATE)


def update_launch_state(
    **changes: object,
) -> None:
    """
    Update one or more launch-state values.
    """

    with LAUNCH_LOCK:
        LAUNCH_STATE.update(changes)


def is_game_running() -> bool:
    """
    Return whether a game is starting or currently active.
    """

    with LAUNCH_LOCK:
        return LAUNCH_STATE["state"] in {
            "starting",
            "running",
        }


def format_mode_name(
    tracking_enabled: bool,
) -> str:
    """
    Return a player-facing launch-mode name.
    """

    if tracking_enabled:
        return "tracked"

    return "untracked"


def run_game_in_background(
    tracking_enabled: bool,
) -> None:
    """
    Launch MAME without blocking the dashboard server.
    """

    mode = format_mode_name(
        tracking_enabled
    )

    started_at = datetime.now()

    update_launch_state(
        state="running",
        mode=mode,
        message=(
            "Tracking active."
            if tracking_enabled
            else "Untracked play active."
        ),
        started_at=started_at.isoformat(),
        ended_at=None,
        return_code=None,
        session_folder=None,
        final_score=None,
    )

    try:
        result = launch_game(
            tracking_enabled=tracking_enabled
        )

    except Exception as error:
        update_launch_state(
            state="error",
            mode=mode,
            message=f"Launch failed: {error}",
            ended_at=datetime.now().isoformat(),
        )

        print(
            "[Dashboard] Game launch failed:"
        )
        print(error)
        return

    finish_launch(
        result=result,
        mode=mode,
    )


def finish_launch(
    result: LaunchResult,
    mode: str,
) -> None:
    """
    Store the result of a completed MAME launch.
    """

    session_folder = None

    if result.session_folder is not None:
        session_folder = str(
            result.session_folder
        )

    if result.tracking_enabled:
        message = (
            "Tracked game finished. "
            "Career statistics have been updated."
        )
    else:
        message = (
            "Untracked game finished. "
            "No tracker session was created."
        )

    update_launch_state(
        state="finished",
        mode=mode,
        message=message,
        ended_at=datetime.now().isoformat(),
        return_code=result.return_code,
        session_folder=session_folder,
        final_score=result.final_score,
    )


def request_game_launch(
    tracking_enabled: bool,
) -> tuple[dict[str, object], HTTPStatus]:
    """
    Start a game unless another game is already active.
    """

    with LAUNCH_LOCK:
        if LAUNCH_STATE["state"] in {
            "starting",
            "running",
        }:
            response = dict(LAUNCH_STATE)

            response["accepted"] = False
            response["message"] = (
                "A game is already running."
            )

            return (
                response,
                HTTPStatus.CONFLICT,
            )

        mode = format_mode_name(
            tracking_enabled
        )

        LAUNCH_STATE.update(
            {
                "state": "starting",
                "mode": mode,
                "message": (
                    "Starting tracked play..."
                    if tracking_enabled
                    else "Starting untracked play..."
                ),
                "started_at": datetime.now().isoformat(),
                "ended_at": None,
                "return_code": None,
                "session_folder": None,
                "final_score": None,
            }
        )

    launch_thread = threading.Thread(
        target=run_game_in_background,
        args=(tracking_enabled,),
        daemon=True,
        name=f"dk-{mode}-launch",
    )

    launch_thread.start()

    return (
        {
            "accepted": True,
            "state": "starting",
            "mode": mode,
            "message": (
                "Starting tracked play..."
                if tracking_enabled
                else "Starting untracked play..."
            ),
        },
        HTTPStatus.ACCEPTED,
    )


# ---------------------------------------------------------
# Live session telemetry
# ---------------------------------------------------------

def parse_iso_datetime(
    value: object,
) -> datetime | None:
    """
    Parse an ISO datetime value safely.
    """

    if not isinstance(value, str):
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def get_session_directories() -> list[Path]:
    """
    Return all existing tracked-session directories.
    """

    if not SESSIONS_FOLDER.exists():
        return []

    try:
        return [
            path
            for path in SESSIONS_FOLDER.iterdir()
            if path.is_dir()
        ]
    except OSError:
        return []


def find_active_session_folder(
    launch_state: dict[str, object],
) -> Path | None:
    """
    Locate the tracked session created for the active game.

    launcher.py creates the session directory immediately
    before MAME starts. The dashboard can therefore identify
    it using the launch start time.
    """

    configured_folder = launch_state.get(
        "session_folder"
    )

    if isinstance(configured_folder, str):
        candidate = Path(configured_folder)

        if candidate.is_dir():
            return candidate

    if launch_state.get("mode") != "tracked":
        return None

    if launch_state.get("state") not in {
        "starting",
        "running",
    }:
        return None

    started_at = parse_iso_datetime(
        launch_state.get("started_at")
    )

    session_directories = (
        get_session_directories()
    )

    if not session_directories:
        return None

    matching_directories: list[
        tuple[float, Path]
    ] = []

    for directory in session_directories:
        try:
            modified_timestamp = (
                directory.stat().st_mtime
            )
        except OSError:
            continue

        if started_at is not None:
            launch_timestamp = (
                started_at.timestamp()
            )

            if modified_timestamp < (
                launch_timestamp - 3.0
            ):
                continue

        matching_directories.append(
            (
                modified_timestamp,
                directory,
            )
        )

    if not matching_directories:
        return None

    matching_directories.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    active_folder = (
        matching_directories[0][1]
    )

    update_launch_state(
        session_folder=str(
            active_folder.resolve()
        )
    )

    return active_folder


def read_live_csv_rows(
    csv_file: Path,
) -> list[dict[str, str]]:
    """
    Read a CSV that may currently be receiving writes.

    Invalid or incomplete rows are ignored rather than
    causing the live endpoint to fail.
    """

    if not csv_file.exists():
        return []

    try:
        with csv_file.open(
            "r",
            newline="",
            encoding="utf-8",
            errors="replace",
        ) as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                return []

            expected_fields = {
                field.strip()
                for field in reader.fieldnames
                if field is not None
            }

            rows: list[dict[str, str]] = []

            for raw_row in reader:
                if raw_row is None:
                    continue

                if None in raw_row:
                    continue

                cleaned_row: dict[str, str] = {}

                for key, value in raw_row.items():
                    if key is None:
                        continue

                    cleaned_key = key.strip()

                    if cleaned_key not in expected_fields:
                        continue

                    cleaned_row[cleaned_key] = (
                        value.strip()
                        if isinstance(value, str)
                        else ""
                    )

                if cleaned_row:
                    rows.append(cleaned_row)

            return rows

    except (
        OSError,
        csv.Error,
        UnicodeError,
    ):
        return []


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


def parse_positive_int(
    value: object,
) -> int | None:
    """
    Parse a positive integer safely.
    """

    parsed = parse_nonnegative_int(
        value
    )

    if parsed is None or parsed <= 0:
        return None

    return parsed


def get_live_score(
    score_rows: list[dict[str, str]],
) -> int:
    """
    Return the newest valid score recorded so far.

    A tracked MAME session may contain multiple games, so
    the current score can legitimately reset to zero.
    """

    for row in reversed(score_rows):
        score = parse_nonnegative_int(
            row.get("score")
        )

        if score is not None:
            return score

    return 0


def format_board_name(
    level: int,
    board_position: int,
    screen_name: str,
) -> str:
    """
    Build a readable board label.
    """

    cleaned_name = (
        screen_name
        .strip()
        .replace("_", " ")
    )

    if (
        cleaned_name
        and cleaned_name != "unknown"
    ):
        return (
            f"{level}-{board_position} "
            f"({cleaned_name})"
        )

    return f"{level}-{board_position}"


def get_current_board(
    event_rows: list[dict[str, str]],
) -> str:
    """
    Return the most recently started board.
    """

    for row in reversed(event_rows):
        if row.get("event") != "board_start":
            continue

        level = parse_positive_int(
            row.get("level")
        )

        board_position = parse_positive_int(
            row.get("board_position")
        )

        if (
            level is None
            or board_position is None
        ):
            continue

        screen_name = row.get(
            "screen_name",
            "unknown",
        )

        return format_board_name(
            level,
            board_position,
            screen_name,
        )

    return "Waiting for game start"


def calculate_elapsed_seconds(
    launch_state: dict[str, object],
) -> int:
    """
    Return elapsed launch time in whole seconds.
    """

    started_at = parse_iso_datetime(
        launch_state.get("started_at")
    )

    if started_at is None:
        return 0

    ended_at = parse_iso_datetime(
        launch_state.get("ended_at")
    )

    comparison_time = (
        ended_at
        if ended_at is not None
        else datetime.now()
    )

    elapsed = (
        comparison_time - started_at
    ).total_seconds()

    return max(
        0,
        int(elapsed),
    )


def build_inactive_live_state(
    launch_state: dict[str, object],
) -> dict[str, object]:
    """
    Return live-state data when tracking is inactive.
    """

    mode = launch_state.get("mode")
    state = launch_state.get("state")

    if (
        mode == "untracked"
        and state in {
            "starting",
            "running",
        }
    ):
        message = (
            "Untracked play is active. "
            "No telemetry is being recorded."
        )
    elif (
        mode == "tracked"
        and state == "starting"
    ):
        message = (
            "Waiting for the tracked session "
            "folder to be created."
        )
    elif (
        mode == "tracked"
        and state == "finished"
    ):
        message = (
            "The tracked session has ended "
            "and is now finalized."
        )
    else:
        message = (
            "Start a tracked game to view "
            "live telemetry."
        )

    return {
        "active": False,
        "tracking": False,
        "state": state,
        "mode": mode,
        "message": message,
        "session_name": None,
        "score": 0,
        "current_board": "Not active",
        "lives_lost": 0,
        "boards_cleared": 0,
        "bonus_lives": 0,
        "elapsed_seconds":
            calculate_elapsed_seconds(
                launch_state
            ),
    }


def get_live_session_state() -> dict[str, object]:
    """
    Build provisional telemetry for the active session.
    """

    launch_state = get_launch_state()

    if launch_state.get("mode") != "tracked":
        return build_inactive_live_state(
            launch_state
        )

    if launch_state.get("state") not in {
        "starting",
        "running",
    }:
        return build_inactive_live_state(
            launch_state
        )

    session_folder = find_active_session_folder(
        launch_state
    )

    if session_folder is None:
        return {
            "active": False,
            "tracking": True,
            "state": launch_state.get(
                "state"
            ),
            "mode": "tracked",
            "message": (
                "Tracking is active. Waiting "
                "for telemetry files."
            ),
            "session_name": None,
            "score": 0,
            "current_board":
                "Waiting for game start",
            "lives_lost": 0,
            "boards_cleared": 0,
            "bonus_lives": 0,
            "elapsed_seconds":
                calculate_elapsed_seconds(
                    launch_state
                ),
        }

    score_file = (
        session_folder / "score_log.csv"
    )

    event_file = (
        session_folder / "events.csv"
    )

    score_rows = read_live_csv_rows(
        score_file
    )

    event_rows = read_live_csv_rows(
        event_file
    )

    return {
        "active": True,
        "tracking": True,
        "state": launch_state.get(
            "state"
        ),
        "mode": "tracked",
        "message": (
            "Live tracked session in progress."
        ),
        "session_name":
            session_folder.name,
        "score": get_live_score(
            score_rows
        ),
        "current_board":
            get_current_board(
                event_rows
            ),
         "lives_remaining":
            get_lives_remaining(
                event_rows
            ),
        "lives_lost":
            count_live_events(
                event_rows,
                "life_lost",
            ),
        "boards_cleared":
            count_live_events(
                event_rows,
                "level_transition",
            ),
        "bonus_lives":
            count_live_events(
                event_rows,
                "bonus_life",
            ),
        "elapsed_seconds":
            calculate_elapsed_seconds(
                launch_state
            ),
    }


# ---------------------------------------------------------
# Dashboard data
# ---------------------------------------------------------

def parse_session_datetime(
    session_name: str,
) -> datetime | None:
    """
    Parse the launch timestamp from a logical session ID.

    Logical sessions use IDs such as
    2026-08-23_11-22-55_03. Legacy launch names without a
    game suffix are also supported.
    """

    launch_name = session_name

    name_parts = session_name.rsplit(
        "_",
        maxsplit=1,
    )

    if (
        len(name_parts) == 2
        and name_parts[1].isdigit()
    ):
        launch_name = name_parts[0]

    try:
        return datetime.strptime(
            launch_name,
            "%Y-%m-%d_%H-%M-%S",
        )
    except ValueError:
        return None


def load_dashboard_data() -> tuple[
    CareerSummary,
    SessionSummary | None,
    str | None,
    str | None,
    list[tuple[str, SessionSummary]],
]:
    """
    Load career data, the latest compatible session,
    and the date the career high was first achieved.
    """

    SESSIONS_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    career = load_game_career(
        SESSIONS_FOLDER
    )

    career_summary = analyze_career(
        career
    )

    if not career.sessions:
        return (
            career_summary,
            None,
            None,
            None,
            [],
        )

    session_summaries = [
        (
            session,
            analyze_session(session),
        )
        for session in career.sessions
    ]

    latest_session, latest_session_summary = max(
        session_summaries,
        key=lambda item:
            item[0].session_id,
    )

    dashboard_sessions = sorted(
        (
            (
                session.session_id,
                summary,
            )
            for session, summary in session_summaries
        ),
        key=lambda item: item[0],
        reverse=True,
    )

    high_score_sessions = [
        session
        for session, summary in session_summaries
        if summary.final_score
        == career_summary.high_score
    ]

    first_high_score_session = min(
        high_score_sessions,
        key=lambda session:
            session.session_id,
    )

    achieved_datetime = parse_session_datetime(
        first_high_score_session.session_id
    )

    if achieved_datetime is not None:
        achieved_hour = (
            achieved_datetime
            .strftime("%I")
            .lstrip("0")
        )

        career_high_achieved = (
            achieved_datetime.strftime("%B ")
            + str(achieved_datetime.day)
            + achieved_datetime.strftime(", %Y at ")
            + achieved_hour
            + achieved_datetime.strftime(":%M %p")
        )
    else:
        career_high_achieved = (
            first_high_score_session.session_id
        )

    return (
        career_summary,
        latest_session_summary,
        latest_session.session_id,
        career_high_achieved,
        dashboard_sessions,
    )


def get_compatible_session_names() -> list[str]:
    """
    Return compatible logical session IDs, newest first.
    """

    career = load_game_career(
        SESSIONS_FOLDER
    )

    return sorted(
        (
            session.session_id
            for session in career.sessions
        ),
        reverse=True,
    )


# ---------------------------------------------------------
# HTML
# ---------------------------------------------------------

def build_dashboard_html() -> str:
    """
    Build the main dashboard page.
    """

    dashboard_settings = (
        load_dashboard_settings()
    )

    performance_history_checked = (
        "checked"
        if dashboard_settings.performance_history_visible
        else ""
    )

    performance_history_hidden = (
        ""
        if dashboard_settings.performance_history_visible
        else "hidden"
    )

    recent_sessions_checked = (
        "checked"
        if dashboard_settings.recent_sessions_visible
        else ""
    )

    recent_sessions_hidden = (
        ""
        if dashboard_settings.recent_sessions_visible
        else "hidden"
    )

    personal_bests_checked = (
        "checked"
        if dashboard_settings.personal_bests_visible
        else ""
    )

    personal_bests_hidden = (
        ""
        if dashboard_settings.personal_bests_visible
        else "hidden"
    )

    career_statistics_checked = (
        "checked"
        if dashboard_settings.career_statistics_visible
        else ""
    )

    career_statistics_hidden = (
        ""
        if dashboard_settings.career_statistics_visible
        else "hidden"
    )

    launch_controls_checked = (
        "checked"
        if dashboard_settings.launch_controls_visible
        else ""
    )

    launch_controls_hidden = (
        ""
        if dashboard_settings.launch_controls_visible
        else "hidden"
    )

    live_session_checked = (
        "checked"
        if dashboard_settings.live_session_visible
        else ""
    )

    live_session_hidden = (
        ""
        if dashboard_settings.live_session_visible
        else "hidden"
    )

    try:
        (
            career_summary,
            latest_session_summary,
            latest_session_name,
            career_high_achieved,
            dashboard_sessions,
        ) = load_dashboard_data()

        excluded_dashboard_sessions = [
            (
                session.session_id,
                analyze_session(session),
            )
            for session
            in load_excluded_game_sessions(
                SESSIONS_FOLDER
            )
        ]

    except (
        FileNotFoundError,
        NotADirectoryError,
        OSError,
        ValueError,
    ) as error:
        return build_error_html(
            title="Dashboard data unavailable",
            message=(
                "Jungle Gym could not load "
                "the career data."
            ),
            details=str(error),
        )

    if latest_session_summary is None:
        last_score = 0
        last_score_class = ""
        latest_session_detail = (
            "Play your first tracked game."
        )
        career_high_detail = (
            "No tracked games yet."
        )
        latest_session_link_html = ""
    else:
        last_score = (
            latest_session_summary.final_score
        )

        last_score_class = (
            "score-extra-large"
            if last_score >= 1_000_000
            else "score-large"
            if last_score >= 100_000
            else ""
        )

        latest_session_detail = (
            "Session: "
            + escape(
                latest_session_name or ""
            )
        )

        career_high_detail = (
            "Achieved "
            + escape(
                career_high_achieved or ""
            )
        )

        latest_session_link_html = """
        <div style="text-align:center; margin-top:18px;">
            <a class="session-link" href="/session">
                View Latest Session
            </a>
        </div>
        """

    recent_session_rows = []

    for session_name, summary in dashboard_sessions[:5]:
        session_datetime = parse_session_datetime(
            session_name
        )

        if session_datetime is not None:
            session_date = (
                session_datetime.strftime("%b ")
                + str(session_datetime.day)
                + session_datetime.strftime(", %Y")
            )
        else:
            session_date = session_name

        furthest_board = (
            summary.furthest_board
            or "—"
        )

        escaped_session_name = escape(
            session_name,
            quote=True,
        )

        recent_session_rows.append(
            f"""
            <article class="recent-session-row">
                <div class="recent-session-main">
                    <p class="recent-session-date">
                        {session_date}
                    </p>

                    <p class="recent-session-board">
                        Furthest board:
                        <span>{furthest_board}</span>
                    </p>
                </div>

                <div class="recent-session-actions">
                    <div class="recent-session-score">
                        <strong>
                            {summary.final_score:,}
                        </strong>

                        <span>
                            {summary.boards_cleared}
                            boards cleared
                        </span>
                    </div>

                    <button
                        class="exclude-session-button"
                        type="button"
                        data-session-name="{escaped_session_name}"
                    >
                        Exclude
                    </button>
                </div>
            </article>
            """
        )

    recent_sessions_html = (
        "\n".join(
            recent_session_rows
        )
        if recent_session_rows
        else """
        <p class="panel-description">
            No tracked sessions yet. Start a tracked game
            to begin building your Jungle Gym career.
        </p>
        """
    )

    excluded_session_rows = []

    for session_name, summary in excluded_dashboard_sessions:
        session_datetime = parse_session_datetime(
            session_name
        )

        if session_datetime is not None:
            session_date = (
                session_datetime.strftime("%b ")
                + str(session_datetime.day)
                + session_datetime.strftime(", %Y")
            )
        else:
            session_date = session_name

        furthest_board = (
            summary.furthest_board
            or "—"
        )

        escaped_session_name = escape(
            session_name,
            quote=True,
        )

        excluded_session_rows.append(
            f"""
            <article class="recent-session-row">
                <div class="recent-session-main">
                    <p class="recent-session-date">
                        {session_date}
                    </p>

                    <p class="recent-session-board">
                        Furthest board:
                        <span>{furthest_board}</span>
                    </p>
                </div>

                <div class="recent-session-actions">
                    <div class="recent-session-score">
                        <strong>
                            {summary.final_score:,}
                        </strong>

                        <span>
                            {summary.boards_cleared}
                            boards cleared
                        </span>
                    </div>

                    <button
                        class="include-session-button"
                        type="button"
                        data-session-name="{escaped_session_name}"
                    >
                        Include
                    </button>
                </div>
            </article>
            """
        )

    if excluded_session_rows:
        excluded_sessions_html = (
            """
            <div class="excluded-sessions-section">
                <h3 class="excluded-sessions-heading">
                    Excluded from Career
                </h3>

                <p class="panel-description">
                    These games are retained in history but
                    do not affect career statistics.
                </p>

                <div class="recent-session-list">
            """
            + "\n".join(
                excluded_session_rows
            )
            + """
                </div>
            </div>
            """
        )
    else:
        excluded_sessions_html = ""

    performance_sessions = list(
        reversed(
            dashboard_sessions[:12]
        )
    )

    performance_max_score = max(
        1,
        max(
            (
                summary.final_score
                for _, summary in performance_sessions
            ),
            default=0,
        ),
    )

    performance_bar_items = []

    for session_name, summary in performance_sessions:
        session_datetime = parse_session_datetime(
            session_name
        )

        if session_datetime is not None:
            session_label = (
                session_datetime.strftime("%b ")
                + str(session_datetime.day)
            )
        else:
            session_label = session_name

        bar_height = max(
            6,
            round(
                summary.final_score
                / performance_max_score
                * 100
            ),
        )

        performance_bar_items.append(
            f"""
            <div class="performance-bar-item">
                <div class="performance-bar-track">
                    <div
                        class="performance-bar"
                        style="height: {bar_height}%;"
                        title="{session_label}: "
                              "{summary.final_score:,}"
                    ></div>
                </div>

                <span class="performance-bar-score">
                    {summary.final_score:,}
                </span>

                <span class="performance-bar-label">
                    {session_label}
                </span>
            </div>
            """
        )

    performance_history_html = (
        "\n".join(
            performance_bar_items
        )
        if performance_bar_items
        else """
        <p class="panel-description">
            Performance history will appear after your
            first tracked game.
        </p>
        """
    )

    best_first_death_score = max(
        (
            summary.first_death_score
            for _, summary in dashboard_sessions
            if summary.first_death_score is not None
        ),
        default=0,
    )

    most_boards_cleared = max(
        (
            summary.boards_cleared
            for _, summary in dashboard_sessions
        ),
        default=0,
    )

    longest_run_seconds = max(
        (
            summary.duration_seconds
            for _, summary in dashboard_sessions
        ),
        default=0,
    )

    longest_run_minutes = round(
        longest_run_seconds / 60
    )

    best_board_points = max(
        (
            board_stat.best_points_gained
            for board_stat in career_summary.board_stats
        ),
        default=0,
    )

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>Jungle Gym</title>

    <style>
        :root {{
            color-scheme: dark;

            font-family:
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;

            --page-background: #000000;
            --panel-background: #030003;
            --card-background: #080008;
            --card-border: #ec3193;

            --primary-text: #fefcff;
            --secondary-text: var(--ladder-primary);

            --girder-primary: #ec3193;
            --girder-highlight: #f057e8;
            --girder-shadow: #8e0305;

            --ladder-primary: #13f3ff;
            --ladder-shadow: #0301dc;

            --barrel-orange: #ee7511;
            --barrel-gold: #f4ba15;

            --score-yellow: #f8f919;
            --bonus-green: #11ef11;
            --danger-red: #e80709;

            --accent: var(--score-yellow);
            --success: var(--bonus-green);
            --danger: var(--danger-red);
            --button-hover: #180018;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            min-height: 100vh;
            margin: 0;
            padding: clamp(
                18px,
                4vw,
                40px
            );
            background:
                radial-gradient(
                    circle at top,
                    #120000 0,
                    var(--page-background) 360px
                );
            color: var(--primary-text);
        }}

        button {{
            font: inherit;
        }}

        main {{
            width: min(100%, 1000px);
            margin: 0 auto;
        }}
        header {{
            position: relative;
            margin-bottom: 32px;
            padding: 28px 20px 30px;
            overflow: hidden;
            border: 2px solid var(--girder-primary);
            border-radius: 10px;
            background:
                linear-gradient(
                    180deg,
                    #080000,
                    #000000
                );
            text-align: center;
            box-shadow:
                0 0 0 3px var(--girder-shadow),
                0 0 20px rgb(236 49 147 / 0.24);
        }}
        header::before,
        header::after {{
            content: "";
            position: absolute;
            left: 0;
            width: 100%;
            height: 10px;
            background:
                repeating-linear-gradient(
                    135deg,
                    var(--girder-highlight) 0 8px,
                    var(--girder-primary) 8px 16px,
                    var(--girder-shadow) 16px 24px
                );
        }}

        header::before {{
            top: 0;
            border-left:
                14px double var(--ladder-primary);
            border-right:
                14px double var(--ladder-primary);
        }}

        header::after {{
            bottom: 0;
            border-left:
                14px double var(--ladder-primary);
            border-right:
                14px double var(--ladder-primary);
        }}

        h1 {{
            margin: 0;
            color: var(--barrel-gold);
            font-family:
                "Courier New",
                monospace;
            font-size: clamp(
                2.4rem,
                8vw,
                5rem
            );
            font-weight: 900;
            line-height: 0.95;
            letter-spacing: 0.08em;
            text-shadow:
                3px 3px 0 var(--barrel-orange),
                0 0 18px rgb(244 186 21 / 0.26);
        }}

        .subtitle {{
            margin: 12px 0 0;
            color: var(--barrel-gold);
            font-family:
                "Courier New",
                monospace;
            font-size: clamp(
                0.78rem,
                2vw,
                1rem
            );
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }}

        .header-actions {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 12px;
            margin-top: 20px;
        }}

        .dashboard-customize-button {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 10px 16px;
            border:
                2px solid
                var(--ladder-primary);
            border-radius: 6px;
            background:
                linear-gradient(
                    180deg,
                    #160016,
                    #050005
                );
            color: var(--barrel-gold);
            font-family:
                "Courier New",
                monospace;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            text-decoration: none;
            cursor: pointer;
            box-shadow:
                0 0 0 2px #000000,
                0 0 12px rgb(41 182 246 / 0.24);
            transition:
                transform 120ms ease,
                border-color 120ms ease,
                color 120ms ease,
                box-shadow 120ms ease;
        }}

        .dashboard-customize-button:hover {{
            border-color: var(--barrel-gold);
            color: #ffffff;
            box-shadow:
                0 0 0 2px #000000,
                0 0 16px rgb(244 186 21 / 0.3);
            transform: translateY(-1px);
        }}

        .dashboard-customize-button:focus-visible {{
            outline:
                3px solid
                var(--barrel-gold);
            outline-offset: 4px;
        }}

        .dashboard-customization-panel[hidden] {{
            display: none;
        }}

        .dashboard-module-list {{
            display: grid;
            gap: 12px;
            margin-top: 20px;
        }}

        .dashboard-module-option {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 16px 18px;
            border:
                1px solid
                var(--card-border);
            border-radius: 8px;
            background: var(--card-background);
            cursor: pointer;
        }}

        .dashboard-module-option:hover {{
            border-color: var(--ladder-primary);
        }}

        .dashboard-module-name {{
            color: var(--primary-text);
            font-weight: 700;
        }}

        .dashboard-module-toggle {{
            width: 22px;
            height: 22px;
            flex: 0 0 auto;
            accent-color: var(--barrel-gold);
            cursor: pointer;
        }}

        .dashboard-customization-actions {{
            display: flex;
            justify-content: flex-end;
            margin-top: 18px;
        }}

        .dashboard-customize-button:disabled {{
            opacity: 0.65;
            cursor: wait;
            transform: none;
        }}

        .dashboard-module[hidden] {{
            display: none;
        }}

        .panel {{
            position: relative;
            margin-bottom: 24px;
            padding: clamp(
                22px,
                3vw,
                30px
            );
            overflow: hidden;
            border:
                2px solid
                var(--girder-primary);
            border-radius: 8px;
            background:
                linear-gradient(
                    180deg,
                    #080008,
                    var(--panel-background)
                );
            box-shadow:
                0 0 0 3px var(--girder-shadow),
                0 10px 30px rgb(0 0 0 / 0.45);
        }}

                .panel::before,
        .panel::after {{
            content: "";
            position: absolute;
            left: 0;
            width: 100%;
            height: 8px;
            pointer-events: none;
            background:
                repeating-linear-gradient(
                    135deg,
                    var(--girder-highlight) 0 7px,
                    var(--girder-primary) 7px 14px,
                    var(--girder-shadow) 14px 21px
                );
        }}

        .panel::before {{
            top: 0;
        }}

        .panel::after {{
            bottom: 0;
        }}

        .panel-heading {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0 0 8px;
            color: var(--girder-primary);
            font-family:
                "Courier New",
                monospace;
            font-size: clamp(
                1rem,
                2.2vw,
                1.25rem
            );
            font-weight: 900;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}

        .panel-heading::before {{
            content: "";
            flex: 0 0 10px;
            width: 10px;
            height: 10px;
            border:
                2px solid
                var(--barrel-gold);
            border-radius: 50%;
            background:
                var(--barrel-orange);
            box-shadow:
                inset 0 0 0 2px #000000;
        }}

        .panel-description {{
            margin: 0 0 20px;
            color: var(--secondary-text);
            line-height: 1.55;
            opacity: 0.88;
        }}

        .launch-buttons {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 14px;
        }}

        .launch-button {{
            min-height: 64px;
            padding: 14px 20px;
            border: 1px solid var(--card-border);
            border-radius: 12px;
            background: var(--card-background);
            color: var(--primary-text);
            cursor: pointer;
            font-weight: 700;
            transition:
                background 120ms ease,
                border-color 120ms ease,
                opacity 120ms ease;
        }}

        .launch-button:hover:not(:disabled) {{
            background: var(--button-hover);
            border-color: var(--accent);
        }}

        .launch-button.primary {{
            border-color: var(--accent);
            color: var(--barrel-gold);
        }}

        .launch-button:disabled {{
            cursor: not-allowed;
            opacity: 0.45;
        }}

        .launch-status {{
            margin-top: 18px;
            padding: 16px;
            border: 1px solid var(--card-border);
            border-radius: 12px;
            background: var(--page-background);
        }}

        .launch-status-row {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .status-indicator {{
            width: 12px;
            height: 12px;
            flex: 0 0 auto;
            border-radius: 50%;
            background: var(--secondary-text);
        }}

        .status-indicator.running {{
            background: var(--success);
        }}

        .status-indicator.finished {{
            background: var(--accent);
        }}

        .status-indicator.error {{
            background: var(--danger);
        }}

        .launch-status-text {{
            margin: 0;
            font-weight: 700;
        }}

        .launch-status-detail {{
            margin: 7px 0 0 22px;
            color: var(--secondary-text);
            font-size: 0.9rem;
        }}

        .live-panel {{
            display: none;
        }}

        .live-panel.visible {{
            display: block;
        }}

        .live-header {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 20px;
        }}

        .live-title-group {{
            min-width: 0;
        }}

        .live-heading {{
            margin: 0;
            font-size: 1.25rem;
        }}

        .live-session-name {{
            margin: 6px 0 0;
            overflow-wrap: anywhere;
            color: var(--secondary-text);
            font-size: 0.9rem;
        }}

        .live-badge {{
            flex: 0 0 auto;
            padding: 7px 10px;
            border: 1px solid var(--success);
            border-radius: 999px;
            color: var(--success);
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .live-grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(150px, 1fr)
                );
            gap: 14px;
        }}

        .live-card {{
            min-height: 112px;
            padding: 18px;
            border: 1px solid var(--card-border);
            border-radius: 12px;
            background: var(--card-background);
        }}

        .live-card.wide {{
            grid-column: span 2;
        }}

        .live-label {{
            margin: 0;
            color: var(--secondary-text);
            font-size: 0.8rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .live-value {{
            margin: 14px 0 0;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.1;
        }}

        .live-value.score {{
            color: var(--accent);
            font-size: clamp(
                2.4rem,
                7vw,
                4rem
            );
        }}

        .live-message {{
            margin: 18px 0 0;
            color: var(--secondary-text);
            text-align: center;
        }}

        .metric-grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(210px, 1fr)
                );
            gap: 18px;
        }}

        .metric-card {{
            position: relative;
            min-height: 170px;
            padding: 26px 24px 24px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow: hidden;
            border:
                1px solid
                var(--girder-primary);
            border-radius: 8px;
            background:
                linear-gradient(
                    180deg,
                    #0b000b,
                    var(--card-background)
                );
            box-shadow:
                inset 0 0 0 1px
                rgb(240 87 232 / 0.12),
                0 8px 24px
                rgb(0 0 0 / 0.4);
        }}
        .metric-card::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 6px;
            background:
                repeating-linear-gradient(
                    135deg,
                    var(--girder-highlight) 0 6px,
                    var(--girder-primary) 6px 12px,
                    var(--girder-shadow) 12px 18px
                );
        }}

        .metric-card::after {{
            content: "";
            position: absolute;
            right: 12px;
            bottom: 12px;
            width: 8px;
            height: 8px;
            border:
                2px solid
                var(--barrel-gold);
            border-radius: 50%;
            background:
                var(--barrel-orange);
            box-shadow:
                inset 0 0 0 2px
                #000000;
        }}
        .metric-card.ladder-motif {{
            padding-left: 54px;
        }}

        .metric-card.ladder-motif::after {{
            right: auto;
            bottom: auto;
            top: 26px;
            left: 18px;
            width: 18px;
            height: calc(100% - 52px);
            border: 0;
            border-radius: 0;
            background:
                repeating-linear-gradient(
                    180deg,
                    transparent 0 10px,
                    var(--ladder-primary) 10px 12px
                );
            box-shadow:
                inset 2px 0 0
                var(--ladder-primary),
                inset -2px 0 0
                var(--ladder-primary);
            opacity: 0.82;
        }}

        .metric-card.barrel-motif::after {{
            content: none;
        }}

                .oilcan-icon {{
            position: absolute;
            right: 16px;
            bottom: 14px;
            width: 56px;
            height: 72px;
            overflow: visible;
            image-rendering: pixelated;
            filter:
                drop-shadow(
                    0 0 6px
                    rgb(83 245 255 / 0.22)
                )
                drop-shadow(
                    0 0 8px
                    rgb(255 122 41 / 0.18)
                );
        }}

        .oilcan-icon .can-body {{
            fill: var(--ladder-cyan);
        }}

        .oilcan-icon .can-dark {{
            fill: #167f9d;
        }}

        .oilcan-icon .can-light {{
            fill: #8df7ff;
        }}

        .oilcan-icon .flame-outer {{
            fill: var(--barrel-orange);
        }}

        .oilcan-icon .flame-inner {{
            fill: var(--score-yellow);
        }}

        .metric-label {{
            margin: 0;
            color: var(--ladder-primary);
            font-family:
                "Courier New",
                monospace;
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}

        .metric-value {{
            margin: 16px 0;
            color: var(--primary-text);
            font-family:
                "Courier New",
                monospace;
            font-size: clamp(
                2rem,
                3.6vw,
                3.1rem
            );
            font-weight: 900;
            line-height: 1;
            letter-spacing: -0.045em;
            white-space: nowrap;
            text-shadow:
                2px 2px 0
                rgb(142 3 5 / 0.65);
        }}

        .metric-value.score-large {{
            font-size: clamp(
                1.9rem,
                3.3vw,
                2.8rem
            );
        }}

        .metric-value.score-extra-large {{
            font-size: clamp(
                1.7rem,
                3vw,
                2.5rem
            );
        }}

        .metric-detail {{
            margin: 0;
            color: var(--secondary-text);
            font-size: 0.9rem;
            line-height: 1.4;
            opacity: 0.88;
        }}

        .highlight {{
            color: var(--score-yellow);
            text-shadow:
                2px 2px 0
                var(--barrel-orange),
                0 0 12px
                rgb(248 249 25 / 0.22);
        }}

        .status-panel {{
            margin-top: 24px;
            padding: 18px 22px;
            border: 1px solid var(--card-border);
            border-radius: 14px;
            background: var(--panel-background);
            color: var(--secondary-text);
            text-align: center;
        }}

        .status-panel strong {{
            color: var(--primary-text);
        }}


        .session-link {{
            display: inline-block;
            margin-top: 18px;
            padding: 12px 18px;
            border: 1px solid var(--score-yellow);
            border-radius: 10px;
            background: var(--card-background);
            color: var(--barrel-gold);
            font-weight: 700;
            text-decoration: none;
        }}

        .session-link:hover {{
            background: var(--button-hover);
        }}

        .recent-sessions {{
            margin-top: 24px;
        }}

        .recent-session-list {{
            display: grid;
            gap: 10px;
        }}

        .recent-session-row {{
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            min-height: 66px;
            padding: 12px 16px;
            overflow: hidden;
            border: 1px solid rgb(236 49 147 / 0.42);
            border-radius: 5px;
            background:
                linear-gradient(
                    90deg,
                    #090009,
                    var(--card-background)
                );
            box-shadow:
                inset 0 0 0 1px
                rgb(240 87 232 / 0.04);
        }}

        .recent-session-row::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background:
                linear-gradient(
                    180deg,
                    var(--girder-highlight),
                    var(--girder-primary),
                    var(--girder-shadow)
                );
            opacity: 0.72;
        }}

        .recent-session-main {{
            min-width: 0;
            padding-left: 4px;
        }}

        .recent-session-date {{
            margin: 0 0 5px;
            color: var(--ladder-primary);
            font-family: "Courier New", monospace;
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .recent-session-board {{
            margin: 0;
            color: var(--primary-text);
            font-size: 0.84rem;
            opacity: 0.9;
        }}

        .recent-session-board span {{
            color: var(--barrel-gold);
            font-family: "Courier New", monospace;
            font-weight: 700;
        }}

        .recent-session-actions {{
            display: flex;
            align-items: center;
            gap: 14px;
            flex-shrink: 0;
        }}

        .recent-session-score {{
            flex-shrink: 0;
            text-align: right;
        }}

        .recent-session-score strong {{
            display: block;
            color: var(--score-yellow);
            font-family: "Courier New", monospace;
            font-size: clamp(1.2rem, 2.4vw, 1.65rem);
            line-height: 1;
            text-shadow:
                1px 1px 0
                var(--barrel-orange);
        }}

        .recent-session-score span {{
            display: block;
            margin-top: 5px;
            color: var(--ladder-primary);
            font-size: 0.74rem;
            opacity: 0.82;
        }}

        .exclude-session-button {{
            padding: 8px 10px;
            border:
                1px solid
                var(--danger-red);
            border-radius: 6px;
            background: #100000;
            color: var(--danger-red);
            cursor: pointer;
            font-family:
                "Courier New",
                monospace;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            transition:
                background 120ms ease,
                color 120ms ease,
                opacity 120ms ease;
        }}

        .exclude-session-button:hover:not(:disabled) {{
            background: var(--danger-red);
            color: #000000;
        }}

        .exclude-session-button:disabled {{
            cursor: not-allowed;
            opacity: 0.45;
        }}

        .include-session-button {{
            padding: 8px 10px;
            border:
                1px solid
                var(--bonus-green);
            border-radius: 6px;
            background: #001000;
            color: var(--bonus-green);
            cursor: pointer;
            font-family:
                "Courier New",
                monospace;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            transition:
                background 120ms ease,
                color 120ms ease,
                opacity 120ms ease;
        }}

        .include-session-button:hover:not(:disabled) {{
            background: var(--bonus-green);
            color: #000000;
        }}

        .include-session-button:disabled {{
            cursor: not-allowed;
            opacity: 0.45;
        }}

        .excluded-sessions-section {{
            margin-top: 26px;
            padding-top: 22px;
            border-top:
                1px solid
                rgb(19 243 255 / 0.28);
        }}

        .excluded-sessions-heading {{
            margin: 0 0 8px;
            color: var(--bonus-green);
            font-family:
                "Courier New",
                monospace;
            font-size: 0.9rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .performance-history {{
            margin-top: 24px;
        }}

        .performance-chart {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(54px, 1fr)
                );
            align-items: end;
            gap: 12px;
            min-height: 280px;
            padding: 24px 18px 18px;
            border: 1px solid rgb(19 243 255 / 0.32);
            border-radius: 6px;
            background:
                linear-gradient(
                    180deg,
                    #050005,
                    #000000
                );
            box-shadow:
                inset 0 0 24px
                rgb(3 1 220 / 0.12);
        }}

        .performance-bar-item {{
            min-width: 0;
            display: grid;
            grid-template-rows:
                190px
                auto
                auto;
            gap: 7px;
            align-items: end;
            text-align: center;
        }}

        .performance-bar-track {{
            position: relative;
            height: 190px;
            overflow: hidden;
            border-bottom:
                3px solid
                var(--girder-primary);
            background:
                repeating-linear-gradient(
                    180deg,
                    transparent 0 37px,
                    rgb(19 243 255 / 0.07) 37px 38px
                );
            box-shadow:
                0 3px 0
                var(--girder-shadow);
        }}

        .performance-bar {{
            position: absolute;
            right: 28%;
            bottom: 0;
            left: 28%;
            min-height: 8px;
            border-left:
                2px solid
                var(--ladder-primary);
            border-right:
                2px solid
                var(--ladder-primary);
            background:
                repeating-linear-gradient(
                    180deg,
                    transparent 0 8px,
                    var(--ladder-primary) 8px 10px
                );
            box-shadow:
                2px 0 0
                var(--ladder-shadow),
                -2px 0 0
                var(--ladder-shadow),
                0 0 10px
                rgb(19 243 255 / 0.16);
        }}

        .performance-bar-score {{
            overflow: hidden;
            color: var(--barrel-gold);
            font-family: "Courier New", monospace;
            font-size: 0.78rem;
            font-weight: 700;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .performance-bar-label {{
            overflow: hidden;
            color: var(--score-yellow);
            font-family: "Courier New", monospace;
            font-size: 0.68rem;
            font-weight: 700;
            text-overflow: ellipsis;
            text-transform: uppercase;
            white-space: nowrap;
            opacity: 0.95;
        }}

        .personal-bests {{
            margin-top: 24px;
        }}

        .personal-best-grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(180px, 1fr)
                );
            gap: 12px;
        }}

        .personal-best-card {{
            position: relative;
            min-height: 118px;
            padding: 18px 18px 16px;
            overflow: hidden;
            border:
                1px solid
                rgb(236 49 147 / 0.5);
            border-radius: 6px;
            background:
                linear-gradient(
                    180deg,
                    #0a000a,
                    var(--card-background)
                );
            box-shadow:
                inset 0 0 0 1px
                rgb(240 87 232 / 0.06);
        }}

        .personal-best-card::before {{
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            left: 0;
            height: 4px;
            background:
                repeating-linear-gradient(
                    135deg,
                    var(--girder-highlight) 0 6px,
                    var(--girder-primary) 6px 12px,
                    var(--girder-shadow) 12px 18px
                );
        }}

        .personal-best-label {{
            margin: 0 0 14px;
            color: var(--ladder-primary);
            font-family: "Courier New", monospace;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}

        .personal-best-value {{
            margin: 0;
            color: var(--barrel-gold);
            font-family: "Courier New", monospace;
            font-size: clamp(1.45rem, 3vw, 2rem);
            font-weight: 900;
            line-height: 1;
            text-shadow:
                1px 1px 0
                var(--barrel-orange);
        }}

        .personal-best-detail {{
            margin: 9px 0 0;
            color: var(--primary-text);
            font-size: 0.78rem;
            opacity: 0.78;
        }}

        @media (max-width: 600px) {{
                    .metric-card.ladder-motif {{
                padding-left: 48px;
            }}

            .metric-card.ladder-motif::after {{
                left: 15px;
            }}
            body {{
                padding: 20px;
            }}
            .panel {{
                padding:
                    22px
                    16px;
            }}

            .panel::before,
            .panel::after {{
                height: 6px;
            }}
            .launch-buttons {{
                grid-template-columns: 1fr;
            }}

            .live-header {{
                flex-direction: column;
            }}

            .live-card.wide {{
                grid-column: span 1;
            }}

            .metric-card {{
                min-height: 145px;
            }}
        }}
    </style>
</head>

<body>
    <main>
        <header>
            <h1>JUNGLE GYM</h1>

            <p class="subtitle">
                Arcade performance and training dashboard
            </p>

            <div class="header-actions">
                <button
                    id="dashboard-customize-button"
                    class="dashboard-customize-button"
                    type="button"
                    aria-controls="dashboard-customization-panel"
                    aria-expanded="false"
                >
                    Customize Dashboard
                </button>

                <a
                    class="dashboard-customize-button"
                    href="/support"
                >
                    Support &amp; Diagnostics
                </a>
            </div>
        </header>

        <section
            id="dashboard-customization-panel"
            class="panel dashboard-customization-panel"
            aria-labelledby="dashboard-customization-heading"
            hidden
        >
            <h2
                id="dashboard-customization-heading"
                class="panel-heading"
            >
                Configure Cabinet
            </h2>

            <p class="panel-description">
                Choose which instruments appear on your
                Jungle Gym dashboard.
            </p>

            <div class="dashboard-module-list">
                <label
                    class="dashboard-module-option"
                    for="performance-history-toggle"
                >
                    <span class="dashboard-module-name">
                        Performance History
                    </span>

                    <input
                        id="performance-history-toggle"
                        class="dashboard-module-toggle"
                        type="checkbox"
                        role="switch"
                        data-setting-name="performance_history_visible"
                        data-panel-id="performance-history-panel"
                        {performance_history_checked}
                    >
                </label>

                <label
                    class="dashboard-module-option"
                    for="recent-sessions-toggle"
                >
                    <span class="dashboard-module-name">
                        Recent Sessions
                    </span>

                    <input
                        id="recent-sessions-toggle"
                        class="dashboard-module-toggle"
                        type="checkbox"
                        role="switch"
                        data-setting-name="recent_sessions_visible"
                        data-panel-id="recent-sessions-panel"
                        {recent_sessions_checked}
                    >
                </label>

                <label
                    class="dashboard-module-option"
                    for="personal-bests-toggle"
                >
                    <span class="dashboard-module-name">
                        Personal Bests
                    </span>

                    <input
                        id="personal-bests-toggle"
                        class="dashboard-module-toggle"
                        type="checkbox"
                        role="switch"
                        data-setting-name="personal_bests_visible"
                        data-panel-id="personal-bests-panel"
                        {personal_bests_checked}
                    >
                </label>

                <label
                    class="dashboard-module-option"
                    for="career-statistics-toggle"
                >
                    <span class="dashboard-module-name">
                        Career Statistics
                    </span>

                    <input
                        id="career-statistics-toggle"
                        class="dashboard-module-toggle"
                        type="checkbox"
                        role="switch"
                        data-setting-name="career_statistics_visible"
                        data-panel-id="career-statistics-panel"
                        {career_statistics_checked}
                    >
                </label>

                <label
                    class="dashboard-module-option"
                    for="launch-controls-toggle"
                >
                    <span class="dashboard-module-name">
                        Play Donkey Kong
                    </span>

                    <input
                        id="launch-controls-toggle"
                        class="dashboard-module-toggle"
                        type="checkbox"
                        role="switch"
                        data-setting-name="launch_controls_visible"
                        data-panel-id="launch-controls-panel"
                        {launch_controls_checked}
                    >
                </label>

                <label
                    class="dashboard-module-option"
                    for="live-session-toggle"
                >
                    <span class="dashboard-module-name">
                        Live Session
                    </span>

                    <input
                        id="live-session-toggle"
                        class="dashboard-module-toggle"
                        type="checkbox"
                        role="switch"
                        data-setting-name="live_session_visible"
                        data-panel-id="live-session-module"
                        {live_session_checked}
                    >
                </label>
            </div>

            <div class="dashboard-customization-actions">
                <button
                    id="dashboard-restore-defaults-button"
                    class="dashboard-customize-button"
                    type="button"
                >
                    Restore Defaults
                </button>
            </div>
        </section>

        <section
            id="launch-controls-panel"
            class="panel dashboard-module"
            aria-labelledby="launch-heading"
            {launch_controls_hidden}
        >
            <h2
                id="launch-heading"
                class="panel-heading"
            >
                Play Donkey Kong
            </h2>

            <p class="panel-description">
                Every game is recorded automatically.
                Individual sessions can be excluded from
                career statistics afterward.
            </p>

            <div class="launch-buttons">
                <button
                    id="play-button"
                    class="launch-button primary"
                    type="button"
                >
                    Play Now
                </button>
            </div>

            <div
                class="launch-status"
                aria-live="polite"
            >
                <div class="launch-status-row">
                    <span
                        id="status-indicator"
                        class="status-indicator"
                        aria-hidden="true"
                    ></span>

                    <p
                        id="launch-status-text"
                        class="launch-status-text"
                    >
                        Ready to play.
                    </p>
                </div>

                <p
                    id="launch-status-detail"
                    class="launch-status-detail"
                >
                    No game is currently running.
                </p>
            </div>
        </section>

        <div
            id="live-session-module"
            class="dashboard-module"
            {live_session_hidden}
        >
            <section
                id="live-panel"
                class="panel live-panel"
                aria-labelledby="live-heading"
                aria-live="polite"
            >
            <div class="live-header">
                <div class="live-title-group">
                    <h2
                        id="live-heading"
                        class="live-heading"
                    >
                        Live Session
                    </h2>

                    <p
                        id="live-session-name"
                        class="live-session-name"
                    >
                        Waiting for telemetry
                    </p>
                </div>

                <span class="live-badge">
                    In Progress
                </span>
            </div>

            <div class="live-grid">
                <article class="live-card wide">
                    <p class="live-label">
                        Current Score
                    </p>

                    <p
                        id="live-score"
                        class="live-value score"
                    >
                        0
                    </p>
                </article>

                <article class="live-card wide">
                    <p class="live-label">
                        Current Board
                    </p>

                    <p
                        id="live-board"
                        class="live-value"
                    >
                        Waiting for game start
                    </p>
                </article>
                <article class="live-card">
                    <p class="live-label">
                        Lives Remaining
                    </p>

                    <p
                        id="live-lives-remaining"
                        class="live-value"
                    >
                        --
                    </p>
                </article>
                <article class="live-card">
                    <p class="live-label">
                        Lives Lost
                    </p>

                    <p
                        id="live-lives-lost"
                        class="live-value"
                    >
                        0
                    </p>
                </article>

                <article class="live-card">
                    <p class="live-label">
                        Boards Cleared
                    </p>

                    <p
                        id="live-boards-cleared"
                        class="live-value"
                    >
                        0
                    </p>
                </article>

                <article class="live-card">
                    <p class="live-label">
                        Bonus Lives
                    </p>

                    <p
                        id="live-bonus-lives"
                        class="live-value"
                    >
                        0
                    </p>
                </article>

                <article class="live-card">
                    <p class="live-label">
                        Elapsed Time
                    </p>

                    <p
                        id="live-elapsed"
                        class="live-value"
                    >
                        00:00
                    </p>
                </article>
            </div>

                <p
                    id="live-message"
                    class="live-message"
                >
                    Live tracked session in progress.
                </p>
            </section>
        </div>

        <section
            id="career-statistics-panel"
            class="metric-grid dashboard-module"
            aria-label="Career statistics"
            {career_statistics_hidden}
        >
            <article class="metric-card">
                <p class="metric-label">
                    Last Score
                </p>

                <p class="metric-value {last_score_class}">
                    {last_score:,}
                </p>

                <p class="metric-detail">
                    {latest_session_detail}
                </p>
            </article>

            <article class="metric-card">
                <p class="metric-label">
                    Career High
                </p>

                <p class="metric-value highlight {
                    "score-extra-large"
                    if career_summary.high_score >= 1_000_000
                    else "score-large"
                    if career_summary.high_score >= 100_000
                    else ""
                }">
                    {career_summary.high_score:,}
                </p>

                <p class="metric-detail">
                    {career_high_detail}
                </p>
            </article>

            <article class="metric-card ladder-motif">
                <p class="metric-label">
                    Tracked Sessions
                </p>

                <p class="metric-value">
                    {career_summary.tracked_sessions}
                </p>

                <p class="metric-detail">
                    {career_summary.completed_games}
                    completed ·
                    {career_summary.quit_or_incomplete_games}
                    incomplete
                </p>
            </article>

            <article class="metric-card barrel-motif">
                            <svg
                    class="oilcan-icon"
                    viewBox="0 0 24 32"
                    role="img"
                    aria-label="Flaming oil can"
                    shape-rendering="crispEdges"
                >
                    <!-- Flame -->
                    <rect
                        class="flame-outer"
                        x="9"
                        y="0"
                        width="2"
                        height="2"
                    />
                    <rect
                        class="flame-outer"
                        x="6"
                        y="2"
                        width="3"
                        height="2"
                    />
                    <rect
                        class="flame-outer"
                        x="12"
                        y="3"
                        width="2"
                        height="2"
                    />
                    <rect
                        class="flame-outer"
                        x="7"
                        y="5"
                        width="8"
                        height="2"
                    />
                    <rect
                        class="flame-outer"
                        x="5"
                        y="7"
                        width="4"
                        height="3"
                    />
                    <rect
                        class="flame-outer"
                        x="13"
                        y="7"
                        width="4"
                        height="3"
                    />
                    <rect
                        class="flame-outer"
                        x="8"
                        y="9"
                        width="7"
                        height="4"
                    />

                    <rect
                        class="flame-inner"
                        x="9"
                        y="5"
                        width="3"
                        height="3"
                    />
                    <rect
                        class="flame-inner"
                        x="7"
                        y="8"
                        width="3"
                        height="3"
                    />
                    <rect
                        class="flame-inner"
                        x="12"
                        y="9"
                        width="3"
                        height="3"
                    />

                    <!-- Can top -->
                    <rect
                        class="can-dark"
                        x="4"
                        y="13"
                        width="16"
                        height="2"
                    />
                    <rect
                        class="can-body"
                        x="3"
                        y="15"
                        width="18"
                        height="14"
                    />

                    <!-- Side pipe -->
                    <rect
                        class="can-dark"
                        x="1"
                        y="15"
                        width="2"
                        height="14"
                    />
                    <rect
                        class="can-light"
                        x="1"
                        y="20"
                        width="2"
                        height="2"
                    />

                    <!-- Can bands -->
                    <rect
                        class="can-light"
                        x="3"
                        y="18"
                        width="18"
                        height="2"
                    />
                    <rect
                        class="can-light"
                        x="3"
                        y="25"
                        width="18"
                        height="2"
                    />

                    <!-- Front panel -->
                    <rect
                        class="can-dark"
                        x="6"
                        y="21"
                        width="12"
                        height="3"
                    />
                    <rect
                        class="can-light"
                        x="8"
                        y="22"
                        width="2"
                        height="1"
                    />
                    <rect
                        class="can-light"
                        x="11"
                        y="22"
                        width="2"
                        height="1"
                    />
                    <rect
                        class="can-light"
                        x="14"
                        y="22"
                        width="2"
                        height="1"
                    />

                    <!-- Feet -->
                    <rect
                        class="can-dark"
                        x="2"
                        y="29"
                        width="4"
                        height="2"
                    />
                    <rect
                        class="can-dark"
                        x="18"
                        y="29"
                        width="4"
                        height="2"
                    />
                </svg>
            <p class="metric-label">
                    Average Score
                </p>

                              <p class="metric-value {
                    "score-extra-large"
                    if career_summary.average_score >= 1_000_000
                    else "score-large"
                    if career_summary.average_score >= 100_000
                    else ""
                }">
                    {career_summary.average_score:,.0f}
                </p>

                <p class="metric-detail">
                    Median:
                    {career_summary.median_score:,.0f}
                </p>
            </article>
        </section>

        <section
            id="personal-bests-panel"
            class="panel personal-bests dashboard-module"
            {personal_bests_hidden}
        >
            <h2 class="panel-heading">
                Personal Bests
            </h2>

            <p class="panel-description">
                Standout records from your tracked runs.
            </p>

            <div class="personal-best-grid">
                <article class="personal-best-card">
                    <p class="personal-best-label">
                        Best First Death
                    </p>

                    <p class="personal-best-value">
                        {best_first_death_score:,}
                    </p>

                    <p class="personal-best-detail">
                        Highest score reached before
                        losing the first life.
                    </p>
                </article>

                <article class="personal-best-card">
                    <p class="personal-best-label">
                        Most Boards Cleared
                    </p>

                    <p class="personal-best-value">
                        {most_boards_cleared}
                    </p>

                    <p class="personal-best-detail">
                        Best single-run board total.
                    </p>
                </article>

                <article class="personal-best-card">
                    <p class="personal-best-label">
                        Longest Run
                    </p>

                    <p class="personal-best-value">
                        {longest_run_minutes} min
                    </p>

                    <p class="personal-best-detail">
                        Longest tracked session.
                    </p>
                </article>

                <article class="personal-best-card">
                    <p class="personal-best-label">
                        Best Board Gain
                    </p>

                    <p class="personal-best-value">
                        {best_board_points:,}
                    </p>

                    <p class="personal-best-detail">
                        Most points gained on one board.
                    </p>
                </article>
            </div>
        </section>

        <section
            id="performance-history-panel"
            class="panel performance-history dashboard-module"
            {performance_history_hidden}
        >
            <h2 class="panel-heading">
                Performance History
            </h2>

            <p class="panel-description">
                Your score progression across the last
                twelve tracked runs.
            </p>

            <div
                class="performance-chart"
                aria-label="Recent score history"
            >
                {performance_history_html}
            </div>
        </section>

        <section
            id="recent-sessions-panel"
            class="panel recent-sessions dashboard-module"
            {recent_sessions_hidden}
        >
            <h2 class="panel-heading">
                Recent Sessions
            </h2>

            <p class="panel-description">
                Your five most recent tracked runs.
            </p>

            <div class="recent-session-list">
                {recent_sessions_html}
            </div>

            {excluded_sessions_html}
        </section>

        {latest_session_link_html}

        <div class="status-panel">
            <strong>Dashboard active.</strong>
            Launch and live telemetry update automatically.
        </div>
    </main>

    <script>
        const playButton =
            document.getElementById(
                "play-button"
            );

        const dashboardCustomizeButton =
            document.getElementById(
                "dashboard-customize-button"
            );

        const dashboardCustomizationPanel =
            document.getElementById(
                "dashboard-customization-panel"
            );

        const dashboardRestoreDefaultsButton =
            document.getElementById(
                "dashboard-restore-defaults-button"
            );

        const dashboardModuleToggles =
            document.querySelectorAll(
                ".dashboard-module-toggle"
            );

        const statusIndicator =
            document.getElementById(
                "status-indicator"
            );

        const statusText =
            document.getElementById(
                "launch-status-text"
            );

        const statusDetail =
            document.getElementById(
                "launch-status-detail"
            );

        const livePanel =
            document.getElementById(
                "live-panel"
            );

        const liveSessionName =
            document.getElementById(
                "live-session-name"
            );

        const liveScore =
            document.getElementById(
                "live-score"
            );

        const liveBoard =
            document.getElementById(
                "live-board"
            );
        const liveLivesRemaining =
            document.getElementById(
                "live-lives-remaining"
            );
        const liveLivesLost =
            document.getElementById(
                "live-lives-lost"
            );

        const liveBoardsCleared =
            document.getElementById(
                "live-boards-cleared"
            );

        const liveBonusLives =
            document.getElementById(
                "live-bonus-lives"
            );

        const liveElapsed =
            document.getElementById(
                "live-elapsed"
            );

        const liveMessage =
            document.getElementById(
                "live-message"
            );

        const excludeSessionButtons =
            document.querySelectorAll(
                ".exclude-session-button"
            );

        const includeSessionButtons =
            document.querySelectorAll(
                ".include-session-button"
            );

        let previousState = null;

        function toggleDashboardCustomization() {{
            const panelIsOpen =
                !dashboardCustomizationPanel.hidden;

            dashboardCustomizationPanel.hidden =
                panelIsOpen;

            dashboardCustomizeButton.setAttribute(
                "aria-expanded",
                String(!panelIsOpen)
            );

            dashboardCustomizeButton.textContent =
                panelIsOpen
                    ? "Customize Dashboard"
                    : "Close Customization";
        }}

        async function saveDashboardModuleVisibility(
            toggle
        ) {{
            const settingName =
                toggle.dataset.settingName;

            const panelId =
                toggle.dataset.panelId;

            const panel =
                document.getElementById(
                    panelId
                );

            if (!settingName || !panel) {{
                return;
            }}

            const previousVisible =
                !panel.hidden;

            const requestedVisible =
                toggle.checked;

            panel.hidden =
                !requestedVisible;

            toggle.disabled = true;

            try {{
                const response = await fetch(
                    "/dashboard/settings",
                    {{
                        method: "POST",
                        headers: {{
                            "Content-Type":
                                "application/json",
                        }},
                        body: JSON.stringify(
                            {{
                                [settingName]:
                                    requestedVisible,
                            }}
                        ),
                    }}
                );

                const result =
                    await response.json();

                if (!response.ok) {{
                    throw new Error(
                        result.message
                        || "Dashboard settings "
                        + "could not be saved."
                    );
                }}

            }} catch (error) {{
                toggle.checked =
                    previousVisible;

                panel.hidden =
                    !previousVisible;

                window.alert(
                    error.message
                    || "Dashboard settings "
                    + "could not be saved."
                );

            }} finally {{
                toggle.disabled = false;
            }}
        }}

        async function restoreDashboardDefaults() {{
            const previousButtonText =
                dashboardRestoreDefaultsButton.textContent;

            dashboardRestoreDefaultsButton.disabled =
                true;

            dashboardRestoreDefaultsButton.textContent =
                "Restoring...";

            dashboardModuleToggles.forEach(
                (toggle) => {{
                    toggle.disabled = true;
                }}
            );

            try {{
                const response = await fetch(
                    "/dashboard/settings/reset",
                    {{
                        method: "POST",
                        headers: {{
                            "Content-Type":
                                "application/json",
                        }},
                        body: JSON.stringify({{}}),
                    }}
                );

                const result =
                    await response.json();

                if (!response.ok) {{
                    throw new Error(
                        result.message
                        || "Dashboard defaults "
                        + "could not be restored."
                    );
                }}

                dashboardModuleToggles.forEach(
                    (toggle) => {{
                        const settingName =
                            toggle.dataset.settingName;

                        const panelId =
                            toggle.dataset.panelId;

                        const panel =
                            document.getElementById(
                                panelId
                            );

                        if (
                            !settingName
                            || !panel
                            || !result.settings
                            || typeof (
                                result.settings[
                                    settingName
                                ]
                            ) !== "boolean"
                        ) {{
                            return;
                        }}

                        const settingValue =
                            result.settings[
                                settingName
                            ];

                        toggle.checked =
                            settingValue;

                        panel.hidden =
                            !settingValue;
                    }}
                );

            }} catch (error) {{
                window.alert(
                    error.message
                    || "Dashboard defaults "
                    + "could not be restored."
                );

            }} finally {{
                dashboardRestoreDefaultsButton.disabled =
                    false;

                dashboardRestoreDefaultsButton.textContent =
                    previousButtonText;

                dashboardModuleToggles.forEach(
                    (toggle) => {{
                        toggle.disabled = false;
                    }}
                );
            }}
        }}

        function setButtonsDisabled(
            disabled
        ) {{
            playButton.disabled = disabled;
        }}

        function getStatusDetail(status) {{
            if (
                status.state === "running"
                || status.state === "starting"
            ) {{
                if (status.mode === "tracked") {{
                    return (
                        "Telemetry is active. "
                        + "This session will be saved "
                        + "when MAME closes."
                    );
                }}

                return (
                    "Telemetry is disabled. "
                    + "This game will not affect "
                    + "career statistics."
                );
            }}

            if (
                status.state === "finished"
                && status.mode === "tracked"
            ) {{
                const score = status.final_score;

                if (
                    score !== null
                    && score !== undefined
                ) {{
                    return (
                        "Final tracked score: "
                        + Number(
                            score
                        ).toLocaleString()
                    );
                }}

                return (
                    "The tracked session was saved."
                );
            }}

            if (
                status.state === "finished"
                && status.mode === "untracked"
            ) {{
                return (
                    "No session folder was created."
                );
            }}

            if (status.state === "error") {{
                return (
                    "Check the terminal running "
                    + "dashboard.py for details."
                );
            }}

            return (
                "No game is currently running."
            );
        }}

        function renderStatus(status) {{
            const state =
                status.state || "ready";

            statusText.textContent = (
                status.message
                || "Ready to play."
            );

            statusDetail.textContent =
                getStatusDetail(status);

            statusIndicator.className = (
                "status-indicator "
                + (
                    state === "starting"
                    ? "running"
                    : state
                )
            );

            const gameActive = (
                state === "starting"
                || state === "running"
            );

            setButtonsDisabled(gameActive);

            const trackedGameJustFinished = (
                (
                    previousState === "running"
                    || previousState === "starting"
                )
                && state === "finished"
                && status.mode === "tracked"
            );

            previousState = state;

            if (trackedGameJustFinished) {{
                window.setTimeout(
                    () =>
                        window.location.reload(),
                    1200
                );
            }}
        }}

        function formatElapsedTime(
            totalSeconds
        ) {{
            const safeSeconds = Math.max(
                0,
                Number(totalSeconds) || 0
            );

            const hours = Math.floor(
                safeSeconds / 3600
            );

            const minutes = Math.floor(
                (
                    safeSeconds % 3600
                ) / 60
            );

            const seconds = Math.floor(
                safeSeconds % 60
            );

            const paddedMinutes = String(
                minutes
            ).padStart(
                2,
                "0"
            );

            const paddedSeconds = String(
                seconds
            ).padStart(
                2,
                "0"
            );

            if (hours > 0) {{
                return (
                    String(hours)
                    + ":"
                    + paddedMinutes
                    + ":"
                    + paddedSeconds
                );
            }}

            return (
                paddedMinutes
                + ":"
                + paddedSeconds
            );
        }}

        function renderLiveState(live) {{
            const shouldShowPanel = (
                live.mode === "tracked"
                && (
                    live.state === "starting"
                    || live.state === "running"
                )
            );

            livePanel.classList.toggle(
                "visible",
                shouldShowPanel
            );

            if (!shouldShowPanel) {{
                return;
            }}

            liveSessionName.textContent = (
                live.session_name
                || "Waiting for telemetry files"
            );

            liveScore.textContent = Number(
                live.score || 0
            ).toLocaleString();

            liveBoard.textContent = (
                live.current_board
                || "Waiting for game start"
            );
                       if (
                live.lives_remaining === null
                || live.lives_remaining === undefined
            ) {{
                liveLivesRemaining.textContent = "--";
            }} else {{
                liveLivesRemaining.textContent =
                    Number(
                        live.lives_remaining
                    ).toLocaleString();
            }}
            liveLivesLost.textContent =
                Number(
                    live.lives_lost || 0
                ).toLocaleString();

            liveBoardsCleared.textContent =
                Number(
                    live.boards_cleared || 0
                ).toLocaleString();

            liveBonusLives.textContent =
                Number(
                    live.bonus_lives || 0
                ).toLocaleString();

            liveElapsed.textContent =
                formatElapsedTime(
                    live.elapsed_seconds
                );

            liveMessage.textContent = (
                live.message
                || "Live tracked session "
                + "in progress."
            );
        }}

        async function fetchStatus() {{
            try {{
                const response = await fetch(
                    "/status",
                    {{
                        cache: "no-store",
                    }}
                );

                if (!response.ok) {{
                    throw new Error(
                        "Status request failed."
                    );
                }}

                const status =
                    await response.json();

                renderStatus(status);

            }} catch (error) {{
                statusText.textContent = (
                    "Dashboard connection "
                    + "unavailable."
                );

                statusDetail.textContent = (
                    "The local dashboard server "
                    + "did not respond."
                );

                statusIndicator.className = (
                    "status-indicator error"
                );

                setButtonsDisabled(false);
            }}
        }}

        async function fetchLiveState() {{
            try {{
                const response = await fetch(
                    "/live",
                    {{
                        cache: "no-store",
                    }}
                );

                if (!response.ok) {{
                    throw new Error(
                        "Live telemetry request "
                        + "failed."
                    );
                }}

                const live =
                    await response.json();

                renderLiveState(live);

            }} catch (error) {{
                liveMessage.textContent = (
                    "Live telemetry is "
                    + "temporarily unavailable."
                );
            }}
        }}

        async function requestLaunch(path) {{
            setButtonsDisabled(true);

            statusText.textContent =
                "Starting MAME...";

            statusDetail.textContent = (
                "Please wait while the game opens."
            );

            statusIndicator.className = (
                "status-indicator running"
            );

            try {{
                const response = await fetch(
                    path,
                    {{
                        method: "POST",
                        headers: {{
                            "Content-Type":
                                "application/json",
                        }},
                    }}
                );

                const status =
                    await response.json();

                renderStatus(status);

                if (!response.ok) {{
                    throw new Error(
                        status.message
                        || "Launch request failed."
                    );
                }}

                await fetchLiveState();

            }} catch (error) {{
                statusText.textContent = (
                    error.message
                    || "Launch request failed."
                );

                statusDetail.textContent = (
                    "Check the terminal running "
                    + "dashboard.py."
                );

                statusIndicator.className = (
                    "status-indicator error"
                );

                await fetchStatus();
            }}
        }}

        async function includeSession(
            button
        ) {{
            const sessionName =
                button.dataset.sessionName;

            if (!sessionName) {{
                return;
            }}

            const confirmed = window.confirm(
                "Include this session in "
                + "career statistics again?"
            );

            if (!confirmed) {{
                return;
            }}

            button.disabled = true;
            button.textContent = "Including...";

            try {{
                const response = await fetch(
                    (
                        "/session/include?name="
                        + encodeURIComponent(
                            sessionName
                        )
                    ),
                    {{
                        method: "POST",
                        headers: {{
                            "Content-Type":
                                "application/json",
                        }},
                    }}
                );

                const result =
                    await response.json();

                if (!response.ok) {{
                    throw new Error(
                        result.message
                        || "Include request failed."
                    );
                }}

                window.location.reload();

            }} catch (error) {{
                button.disabled = false;
                button.textContent = "Include";

                window.alert(
                    error.message
                    || "The session could not "
                    + "be included."
                );
            }}
        }}

        async function excludeSession(
            button
        ) {{
            const sessionName =
                button.dataset.sessionName;

            if (!sessionName) {{
                return;
            }}

            const confirmed = window.confirm(
                "Exclude this session from "
                + "career statistics?"
            );

            if (!confirmed) {{
                return;
            }}

            button.disabled = true;
            button.textContent = "Excluding...";

            try {{
                const response = await fetch(
                    (
                        "/session/exclude?name="
                        + encodeURIComponent(
                            sessionName
                        )
                    ),
                    {{
                        method: "POST",
                        headers: {{
                            "Content-Type":
                                "application/json",
                        }},
                    }}
                );

                const result =
                    await response.json();

                if (!response.ok) {{
                    throw new Error(
                        result.message
                        || "Exclusion request failed."
                    );
                }}

                window.location.reload();

            }} catch (error) {{
                button.disabled = false;
                button.textContent = "Exclude";

                window.alert(
                    error.message
                    || "The session could not "
                    + "be excluded."
                );
            }}
        }}

        dashboardCustomizeButton.addEventListener(
            "click",
            toggleDashboardCustomization
        );

        dashboardRestoreDefaultsButton.addEventListener(
            "click",
            restoreDashboardDefaults
        );

        dashboardModuleToggles.forEach(
            (toggle) => {{
                toggle.addEventListener(
                    "change",
                    () => saveDashboardModuleVisibility(
                        toggle
                    )
                );
            }}
        );

        playButton.addEventListener(
            "click",
            () => requestLaunch(
                "/launch/play"
            )
        );

        excludeSessionButtons.forEach(
            (button) => {{
                button.addEventListener(
                    "click",
                    () => excludeSession(
                        button
                    )
                );
            }}
        );

        includeSessionButtons.forEach(
            (button) => {{
                button.addEventListener(
                    "click",
                    () => includeSession(
                        button
                    )
                );
            }}
        );

        fetchStatus();
        fetchLiveState();

        window.setInterval(
            fetchStatus,
            1000
        );

        window.setInterval(
            fetchLiveState,
            1000
        );
    </script>
</body>
</html>
"""


def build_error_html(
    title: str,
    message: str,
    details: str,
) -> str:
    """
    Build a human-readable error page.
    """

    safe_title = escape(title)
    safe_message = escape(message)
    safe_details = escape(details)

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>{safe_title}</title>

    <style>
        :root {{
            color-scheme: dark;

            font-family:
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }}

        body {{
            min-height: 100vh;
            margin: 0;
            padding: 32px;
            display: grid;
            place-items: center;
            background: #101218;
            color: #f7f8fa;
        }}

        main {{
            width: min(100%, 700px);
            padding: 32px;
            border: 1px solid #4a3232;
            border-radius: 16px;
            background: #231a1d;
        }}

        h1 {{
            margin-top: 0;
        }}

        pre {{
            margin-bottom: 0;
            padding: 16px;
            overflow-wrap: anywhere;
            white-space: pre-wrap;
            border-radius: 10px;
            background: #151218;
            color: #f0b8b8;
        }}
    </style>
</head>

<body>
    <main>
        <h1>{safe_title}</h1>

        <p>{safe_message}</p>

        <pre>{safe_details}</pre>
    </main>
</body>
</html>
"""


def build_not_found_html(
    requested_path: str,
) -> str:
    """
    Build the page shown for an unknown route.
    """

    return build_error_html(
        title="Page not found",
        message=(
            "Jungle Gym does not have a page "
            "at this address."
        ),
        details=requested_path,
    )


def open_folder(
    folder_path: Path,
) -> None:
    """
    Open a folder in the platform's file manager.
    """

    folder_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    if sys.platform == "darwin":
        subprocess.Popen(
            [
                "open",
                str(folder_path),
            ]
        )
        return

    if os.name == "nt":
        os.startfile(
            str(folder_path)
        )
        return

    subprocess.Popen(
        [
            "xdg-open",
            str(folder_path),
        ]
    )


# ---------------------------------------------------------
# HTTP request handling
# ---------------------------------------------------------

class DashboardRequestHandler(
    BaseHTTPRequestHandler
):
    """
    Handle browser requests for the dashboard.
    """

    def do_GET(self) -> None:
        requested_path = (
            self.get_requested_path()
        )

        routes = {
            "/":
                self.serve_dashboard,
            "/index.html":
                self.serve_dashboard,
            "/session":
                self.serve_session,
            "/support":
                self.serve_support,
            "/support/open-data":
                self.serve_open_data_folder,
            "/static/chart.umd.min.js":
                self.serve_chart_js,
            "/status":
                self.serve_status,
            "/live":
                self.serve_live,
        }

        route_handler = routes.get(
            requested_path
        )

        if route_handler is None:
            self.serve_not_found(
                requested_path
            )
            return

        route_handler()

    def do_POST(self) -> None:
        requested_path = (
            self.get_requested_path()
        )

        routes = {
            "/launch/play":
                self.launch_game,
            "/dashboard/settings":
                self.save_dashboard_preferences,
            "/dashboard/settings/reset":
                self.restore_dashboard_defaults,
            "/session/exclude":
                self.exclude_session,
            "/session/include":
                self.include_session,
        }

        route_handler = routes.get(
            requested_path
        )

        if route_handler is None:
            self.serve_not_found(
                requested_path
            )
            return

        route_handler()

    def get_requested_path(self) -> str:
        """
        Return the path without its query string.
        """

        return self.path.split(
            "?",
            maxsplit=1,
        )[0]

    def serve_dashboard(self) -> None:
        """
        Serve setup or the main dashboard.
        """

        config = load_config()
        problems = validate_config(config)

        if problems:
            self.send_html(
                build_setup_page(problems)
            )
            return

        self.send_html(
            build_dashboard_html()
        )

    def serve_chart_js(self) -> None:
        """
        Serve the bundled Chart.js browser build.
        """

        self.send_javascript(
            CHART_JS_FILE
        )

    def serve_support(self) -> None:
        """
        Serve read-only support diagnostics.
        """

        self.send_html(
            build_support_page()
        )

    def serve_open_data_folder(self) -> None:
        """
        Open Jungle Gym's user-data folder.
        """

        try:
            open_folder(
                USER_DATA_FOLDER
            )

        except OSError as error:
            self.send_html(
                build_error_html(
                    title="Data folder unavailable",
                    message=(
                        "Jungle Gym could not open "
                        "the user-data folder."
                    ),
                    details=str(error),
                ),
                status=(
                    HTTPStatus.INTERNAL_SERVER_ERROR
                ),
            )
            return

        self.send_html(
            build_support_page()
        )

    def serve_session(self) -> None:
        """
        Serve details for the requested or latest logical game.
        """

        try:
            career = load_game_career(
                SESSIONS_FOLDER
            )

            sessions_by_name = {
                session.session_id: session
                for session in career.sessions
            }

            session_names = sorted(
                sessions_by_name,
                reverse=True,
            )

            if not session_names:
                raise ValueError(
                    "No compatible sessions are available."
                )

            parsed_url = urlparse(self.path)
            query_values = parse_qs(
                parsed_url.query
            )

            requested_names = query_values.get(
                "name",
                [],
            )

            if requested_names:
                session_name = requested_names[0]

                if session_name not in sessions_by_name:
                    raise ValueError(
                        "The requested session does not "
                        "exist or is not compatible."
                    )
            else:
                session_name = session_names[0]

            session = sessions_by_name[
                session_name
            ]

            session_detail = (
                build_session_detail_from_session(
                    session
                )
            )

            career_summary = analyze_career(
                career
            )

            session_detail["personal_bests"] = (
                build_personal_bests(
                    session_detail,
                    career_summary.high_score,
                )
            )

        except (
            FileNotFoundError,
            NotADirectoryError,
            OSError,
            ValueError,
        ) as error:
            self.send_html(
                build_error_html(
                    title="Session data unavailable",
                    message=(
                        "Jungle Gym could not load "
                        "the requested session."
                    ),
                    details=str(error),
                )
            )
            return

        self.send_html(
            build_session_page(
                session_name,
                session_detail,
                session_names,
            )
        )

    def serve_status(self) -> None:
        """
        Return launcher state as JSON.
        """

        self.send_json(
            get_launch_state()
        )

    def serve_live(self) -> None:
        """
        Return provisional live telemetry.
        """

        self.send_json(
            get_live_session_state()
        )

    def save_dashboard_preferences(self) -> None:
        """
        Save dashboard module visibility preferences.
        """

        try:
            content_length = int(
                self.headers.get(
                    "Content-Length",
                    "0",
                )
            )

            request_body = self.rfile.read(
                content_length
            )

            payload = json.loads(
                request_body.decode("utf-8")
            )

        except (
            ValueError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            self.send_json(
                {
                    "success": False,
                    "message": (
                        "The dashboard settings "
                        "request was invalid."
                    ),
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        if not isinstance(payload, dict):
            self.send_json(
                {
                    "success": False,
                    "message": (
                        "Dashboard settings must "
                        "be a JSON object."
                    ),
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        allowed_settings = {
            "launch_controls_visible",
            "live_session_visible",
            "career_statistics_visible",
            "personal_bests_visible",
            "performance_history_visible",
            "recent_sessions_visible",
        }

        supplied_settings = (
            set(payload)
            & allowed_settings
        )

        if not supplied_settings:
            self.send_json(
                {
                    "success": False,
                    "message": (
                        "No recognized dashboard "
                        "setting was provided."
                    ),
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        for setting_name in supplied_settings:
            if not isinstance(
                payload[setting_name],
                bool,
            ):
                self.send_json(
                    {
                        "success": False,
                        "message": (
                            f"{setting_name} must "
                            "be true or false."
                        ),
                    },
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

        current_settings = (
            load_dashboard_settings()
        )

        updated_values = {
            "launch_controls_visible": (
                current_settings
                .launch_controls_visible
            ),
            "live_session_visible": (
                current_settings
                .live_session_visible
            ),
            "career_statistics_visible": (
                current_settings
                .career_statistics_visible
            ),
            "personal_bests_visible": (
                current_settings
                .personal_bests_visible
            ),
            "performance_history_visible": (
                current_settings
                .performance_history_visible
            ),
            "recent_sessions_visible": (
                current_settings
                .recent_sessions_visible
            ),
        }

        for setting_name in supplied_settings:
            updated_values[setting_name] = (
                payload[setting_name]
            )

        settings = DashboardSettings(
            **updated_values
        )

        try:
            save_dashboard_settings(settings)

        except OSError as error:
            self.send_json(
                {
                    "success": False,
                    "message": (
                        "Dashboard settings could "
                        "not be saved."
                    ),
                    "details": str(error),
                },
                status=(
                    HTTPStatus.INTERNAL_SERVER_ERROR
                ),
            )
            return

        self.send_json(
            {
                "success": True,
                "settings": updated_values,
            }
        )

    def restore_dashboard_defaults(self) -> None:
        """
        Restore default dashboard module visibility.
        """

        settings = DashboardSettings()

        default_values = {
            "launch_controls_visible": (
                settings.launch_controls_visible
            ),
            "live_session_visible": (
                settings.live_session_visible
            ),
            "career_statistics_visible": (
                settings.career_statistics_visible
            ),
            "personal_bests_visible": (
                settings.personal_bests_visible
            ),
            "performance_history_visible": (
                settings.performance_history_visible
            ),
            "recent_sessions_visible": (
                settings.recent_sessions_visible
            ),
        }

        try:
            save_dashboard_settings(settings)

        except OSError as error:
            self.send_json(
                {
                    "success": False,
                    "message": (
                        "Dashboard defaults could "
                        "not be restored."
                    ),
                    "details": str(error),
                },
                status=(
                    HTTPStatus.INTERNAL_SERVER_ERROR
                ),
            )
            return

        self.send_json(
            {
                "success": True,
                "settings": default_values,
            }
        )

    def launch_game(self) -> None:
        """
        Start Donkey Kong with telemetry enabled.
        """

        response, status = (
            request_game_launch(
                tracking_enabled=True
            )
        )

        self.send_json(
            response,
            status=status,
        )

    def exclude_session(self) -> None:
        """
        Exclude one logical game from career analytics.
        """

        parsed_url = urlparse(self.path)
        query_values = parse_qs(
            parsed_url.query
        )

        requested_names = query_values.get(
            "name",
            [],
        )

        if not requested_names:
            self.send_json(
                {
                    "success": False,
                    "message": (
                        "No session name was provided."
                    ),
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        session_name = requested_names[0]

        try:
            set_game_excluded(
                SESSIONS_FOLDER,
                session_name,
                True,
            )

        except (
            FileNotFoundError,
            NotADirectoryError,
            OSError,
            ValueError,
        ) as error:
            self.send_json(
                {
                    "success": False,
                    "message": (
                        "The session could not "
                        "be excluded."
                    ),
                    "details": str(error),
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        self.send_json(
            {
                "success": True,
                "message": (
                    "Session excluded from "
                    "career statistics."
                ),
                "session_name": session_name,
            }
        )

    def include_session(self) -> None:
        """
        Re-include one logical game in career analytics.
        """

        parsed_url = urlparse(self.path)
        query_values = parse_qs(
            parsed_url.query
        )

        requested_names = query_values.get(
            "name",
            [],
        )

        if not requested_names:
            self.send_json(
                {
                    "success": False,
                    "message": (
                        "No session name was provided."
                    ),
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        session_name = requested_names[0]

        try:
            set_game_excluded(
                SESSIONS_FOLDER,
                session_name,
                False,
            )

        except (
            FileNotFoundError,
            NotADirectoryError,
            OSError,
            ValueError,
        ) as error:
            self.send_json(
                {
                    "success": False,
                    "message": (
                        "The session could not "
                        "be included."
                    ),
                    "details": str(error),
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        self.send_json(
            {
                "success": True,
                "message": (
                    "Session included in "
                    "career statistics."
                ),
                "session_name": session_name,
            }
        )

    def serve_not_found(
        self,
        requested_path: str,
    ) -> None:
        """
        Serve an HTML 404 response.
        """

        self.send_html(
            build_not_found_html(
                requested_path
            ),
            status=HTTPStatus.NOT_FOUND,
        )

    def send_html(
        self,
        html: str,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        """
        Send an HTML response.
        """

        response_body = html.encode(
            "utf-8"
        )

        self.send_response(
            status.value
        )

        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8",
        )

        self.send_header(
            "Content-Length",
            str(len(response_body)),
        )

        self.send_header(
            "Cache-Control",
            "no-store",
        )

        self.end_headers()
        self.wfile.write(response_body)

    def send_javascript(
        self,
        file_path: Path,
    ) -> None:
        """
        Send a local JavaScript file.
        """

        try:
            response_body = file_path.read_bytes()

        except OSError as error:
            response_body = (
                "console.error("
                + json.dumps(
                    (
                        "Jungle Gym could not load "
                        f"Chart.js: {error}"
                    )
                )
                + ");"
            ).encode(
                "utf-8"
            )

            self.send_response(
                HTTPStatus.NOT_FOUND.value
            )

        else:
            self.send_response(
                HTTPStatus.OK.value
            )

        self.send_header(
            "Content-Type",
            "application/javascript; charset=utf-8",
        )

        self.send_header(
            "Content-Length",
            str(len(response_body)),
        )

        self.send_header(
            "Cache-Control",
            "no-store",
        )

        self.end_headers()
        self.wfile.write(response_body)

    def send_json(
        self,
        payload: dict[str, object],
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        """
        Send a JSON response.
        """

        response_body = json.dumps(
            payload
        ).encode(
            "utf-8"
        )

        self.send_response(
            status.value
        )

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )

        self.send_header(
            "Content-Length",
            str(len(response_body)),
        )

        self.send_header(
            "Cache-Control",
            "no-store",
        )

        self.end_headers()
        self.wfile.write(response_body)

    def log_message(
        self,
        format_string: str,
        *arguments: object,
    ) -> None:
        message = (
            format_string % arguments
        )

        print(
            f"[Dashboard] {message}"
        )


# ---------------------------------------------------------
# Server startup
# ---------------------------------------------------------

def open_browser() -> None:
    """
    Open the dashboard after startup.
    """

    dashboard_url = (
        f"http://{HOST}:{PORT}"
    )

    timer = threading.Timer(
        0.5,
        webbrowser.open,
        args=(dashboard_url,),
    )

    timer.daemon = True
    timer.start()


def create_dashboard_server() -> ThreadingHTTPServer:
    """
    Create and return the local dashboard server.
    """

    server_address = (
        HOST,
        PORT,
    )

    return ThreadingHTTPServer(
        server_address,
        DashboardRequestHandler,
    )


def run_dashboard() -> None:
    """
    Start the dashboard server and open it in a browser.
    """

    try:
        server = create_dashboard_server()

    except OSError as error:
        print(
            "Could not start Jungle Gym "
            f"dashboard on port {PORT}."
        )
        print(error)
        return

    dashboard_url = (
        f"http://{HOST}:{PORT}"
    )

    print("===================================")
    print(" Jungle Gym Dashboard")
    print("===================================")
    print()
    print(
        f"Career data: {SESSIONS_FOLDER}"
    )
    print(
        f"Running at : {dashboard_url}"
    )
    print(
        "Live route: "
        f"{dashboard_url}/live"
    )
    print("Press Control-C to stop.")
    print()

    open_browser()

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print()
        print("Stopping dashboard...")

    finally:
        server.server_close()
        print("Dashboard stopped.")

