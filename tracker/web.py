from datetime import datetime
from html import escape
from http import HTTPStatus
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
import json
from pathlib import Path
import threading
import webbrowser

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
from tracker.parser import load_career


HOST = "127.0.0.1"
PORT = 5000

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SESSIONS_FOLDER = PROJECT_ROOT / "data" / "sessions"


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
    Return whether a tracked or untracked game is active.
    """

    with LAUNCH_LOCK:
        return LAUNCH_STATE["state"] == "running"


def format_mode_name(
    tracking_enabled: bool,
) -> str:
    """
    Return a player-facing name for the launch mode.
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

    update_launch_state(
        state="running",
        mode=mode,
        message=(
            "Tracking active."
            if tracking_enabled
            else "Untracked play active."
        ),
        started_at=datetime.now().isoformat(),
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
        if LAUNCH_STATE["state"] == "running":
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
                "started_at": None,
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
# Dashboard data
# ---------------------------------------------------------

def load_dashboard_data() -> tuple[
    CareerSummary,
    SessionSummary,
    str,
]:
    """
    Load the career summary and most recent compatible session.
    """

    career = load_career(
        SESSIONS_FOLDER
    )

    career_summary = analyze_career(
        career
    )

    if not career.sessions:
        raise ValueError(
            "No compatible sessions are available "
            "for the dashboard."
        )

    latest_session = max(
        career.sessions,
        key=lambda session: session.folder.name,
    )

    latest_session_summary = analyze_session(
        latest_session
    )

    return (
        career_summary,
        latest_session_summary,
        latest_session.folder.name,
    )


# ---------------------------------------------------------
# HTML
# ---------------------------------------------------------

def build_dashboard_html() -> str:
    """
    Build the main dashboard page using current career data.
    """

    try:
        (
            career_summary,
            latest_session_summary,
            latest_session_name,
        ) = load_dashboard_data()

    except (
        FileNotFoundError,
        NotADirectoryError,
        OSError,
        ValueError,
    ) as error:
        return build_error_html(
            title="Dashboard data unavailable",
            message=(
                "DK Tracker could not load "
                "the career data."
            ),
            details=str(error),
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

    <title>DK Tracker</title>

    <style>
        :root {{
            color-scheme: dark;

            font-family:
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;

            --page-background: #101218;
            --panel-background: #1a1d25;
            --card-background: #222630;
            --card-border: #343a47;
            --primary-text: #f7f8fa;
            --secondary-text: #abb3c0;
            --accent: #e8b84a;
            --success: #62c98c;
            --danger: #ef7b7b;
            --button-hover: #303644;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            min-height: 100vh;
            margin: 0;
            padding: 32px;
            background: var(--page-background);
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
            margin-bottom: 32px;
            text-align: center;
        }}

        h1 {{
            margin: 0;
            font-size: clamp(2.4rem, 8vw, 5rem);
            letter-spacing: 0.08em;
        }}

        .subtitle {{
            margin: 8px 0 0;
            color: var(--secondary-text);
        }}

        .launch-panel {{
            margin-bottom: 24px;
            padding: 24px;
            border: 1px solid var(--card-border);
            border-radius: 16px;
            background: var(--panel-background);
        }}

        .launch-heading {{
            margin: 0 0 8px;
            font-size: 1.25rem;
        }}

        .launch-description {{
            margin: 0 0 20px;
            color: var(--secondary-text);
        }}

        .launch-buttons {{
            display: grid;
            grid-template-columns:
                repeat(
                    2,
                    minmax(0, 1fr)
                );
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
            color: var(--accent);
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
            min-height: 170px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            border: 1px solid var(--card-border);
            border-radius: 16px;
            background: var(--card-background);
        }}

        .metric-label {{
            margin: 0;
            color: var(--secondary-text);
            font-size: 0.95rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .metric-value {{
            margin: 16px 0;
            color: var(--primary-text);
            font-size: clamp(2.3rem, 7vw, 4rem);
            font-weight: 700;
            line-height: 1;
        }}

        .metric-detail {{
            margin: 0;
            color: var(--secondary-text);
            font-size: 0.9rem;
        }}

        .highlight {{
            color: var(--accent);
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

        @media (max-width: 600px) {{
            body {{
                padding: 20px;
            }}

            .launch-buttons {{
                grid-template-columns: 1fr;
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
            <h1>DK TRACKER</h1>

            <p class="subtitle">
                Donkey Kong performance dashboard
            </p>
        </header>

        <section
            class="launch-panel"
            aria-labelledby="launch-heading"
        >
            <h2
                id="launch-heading"
                class="launch-heading"
            >
                Play Donkey Kong
            </h2>

            <p class="launch-description">
                Choose whether this game should be recorded
                in your DK Tracker career statistics.
            </p>

            <div class="launch-buttons">
                <button
                    id="tracked-button"
                    class="launch-button primary"
                    type="button"
                >
                    Play with Tracking
                </button>

                <button
                    id="untracked-button"
                    class="launch-button"
                    type="button"
                >
                    Play without Tracking
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

        <section
            class="metric-grid"
            aria-label="Career statistics"
        >
            <article class="metric-card">
                <p class="metric-label">
                    Last Score
                </p>

                <p class="metric-value">
                    {latest_session_summary.final_score:,}
                </p>

                <p class="metric-detail">
                    Session:
                    {escape(latest_session_name)}
                </p>
            </article>

            <article class="metric-card">
                <p class="metric-label">
                    Career High
                </p>

                <p class="metric-value highlight">
                    {career_summary.high_score:,}
                </p>

                <p class="metric-detail">
                    Highest compatible tracked score
                </p>
            </article>

            <article class="metric-card">
                <p class="metric-label">
                    Tracked Sessions
                </p>

                <p class="metric-value">
                    {career_summary.tracked_sessions}
                </p>

                <p class="metric-detail">
                    {career_summary.skipped_sessions}
                    legacy session(s) excluded
                </p>
            </article>

            <article class="metric-card">
                <p class="metric-label">
                    Average Score
                </p>

                <p class="metric-value">
                    {career_summary.average_score:,.0f}
                </p>

                <p class="metric-detail">
                    Median:
                    {career_summary.median_score:,.0f}
                </p>
            </article>
        </section>

        <div class="status-panel">
            <strong>Dashboard active.</strong>
            Launch status updates automatically.
        </div>
    </main>

    <script>
        const trackedButton = document.getElementById(
            "tracked-button"
        );

        const untrackedButton = document.getElementById(
            "untracked-button"
        );

        const statusIndicator = document.getElementById(
            "status-indicator"
        );

        const statusText = document.getElementById(
            "launch-status-text"
        );

        const statusDetail = document.getElementById(
            "launch-status-detail"
        );

        let previousState = null;
        let previousMode = null;

        function setButtonsDisabled(disabled) {{
            trackedButton.disabled = disabled;
            untrackedButton.disabled = disabled;
        }}

        function getStatusDetail(status) {{
            if (
                status.state === "running"
                || status.state === "starting"
            ) {{
                if (status.mode === "tracked") {{
                    return (
                        "Telemetry is active. "
                        + "This session will be saved when MAME closes."
                    );
                }}

                return (
                    "Telemetry is disabled. "
                    + "This game will not affect career statistics."
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
                        + Number(score).toLocaleString()
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
                    "Check the terminal running dashboard.py "
                    + "for additional details."
                );
            }}

            return "No game is currently running.";
        }}

        function renderStatus(status) {{
            const state = status.state || "ready";

            statusText.textContent = (
                status.message || "Ready to play."
            );

            statusDetail.textContent = getStatusDetail(
                status
            );

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
                previousState === "running"
                && state === "finished"
                && status.mode === "tracked"
            );

            previousState = state;
            previousMode = status.mode;

            if (trackedGameJustFinished) {{
                window.setTimeout(
                    () => window.location.reload(),
                    1200
                );
            }}
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

                const status = await response.json();
                renderStatus(status);

            }} catch (error) {{
                statusText.textContent = (
                    "Dashboard connection unavailable."
                );

                statusDetail.textContent = (
                    "The local dashboard server did not respond."
                );

                statusIndicator.className = (
                    "status-indicator error"
                );

                setButtonsDisabled(false);
            }}
        }}

        async function requestLaunch(path) {{
            setButtonsDisabled(true);

            statusText.textContent = "Starting MAME...";
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

                const status = await response.json();
                renderStatus(status);

                if (!response.ok) {{
                    throw new Error(
                        status.message
                        || "Launch request failed."
                    );
                }}

            }} catch (error) {{
                statusText.textContent = (
                    error.message
                    || "Launch request failed."
                );

                statusDetail.textContent = (
                    "Check the terminal running dashboard.py."
                );

                statusIndicator.className = (
                    "status-indicator error"
                );

                await fetchStatus();
            }}
        }}

        trackedButton.addEventListener(
            "click",
            () => requestLaunch(
                "/launch/tracked"
            )
        );

        untrackedButton.addEventListener(
            "click",
            () => requestLaunch(
                "/launch/untracked"
            )
        );

        fetchStatus();

        window.setInterval(
            fetchStatus,
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
            "DK Tracker does not have a page "
            "at this address."
        ),
        details=requested_path,
    )


# ---------------------------------------------------------
# HTTP request handling
# ---------------------------------------------------------

class DashboardRequestHandler(
    BaseHTTPRequestHandler
):
    """
    Handle browser requests for the local dashboard.
    """

    def do_GET(self) -> None:
        requested_path = self.get_requested_path()

        routes = {
            "/": self.serve_dashboard,
            "/index.html": self.serve_dashboard,
            "/status": self.serve_status,
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
        requested_path = self.get_requested_path()

        routes = {
            "/launch/tracked":
                self.launch_tracked_game,
            "/launch/untracked":
                self.launch_untracked_game,
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
        Return the URL path without its query string.
        """

        return self.path.split(
            "?",
            maxsplit=1,
        )[0]

    def serve_dashboard(self) -> None:
        """
        Serve the main DK Tracker dashboard.
        """

        self.send_html(
            build_dashboard_html()
        )

    def serve_status(self) -> None:
        """
        Return the current launcher state as JSON.
        """

        self.send_json(
            get_launch_state()
        )

    def launch_tracked_game(self) -> None:
        """
        Start Donkey Kong with telemetry enabled.
        """

        response, status = request_game_launch(
            tracking_enabled=True
        )

        self.send_json(
            response,
            status=status,
        )

    def launch_untracked_game(self) -> None:
        """
        Start Donkey Kong without telemetry.
        """

        response, status = request_game_launch(
            tracking_enabled=False
        )

        self.send_json(
            response,
            status=status,
        )

    def serve_not_found(
        self,
        requested_path: str,
    ) -> None:
        """
        Serve a 404 response for an unknown route.
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
        Send an HTML response to the browser.
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

    def send_json(
        self,
        payload: dict[str, object],
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        """
        Send a JSON response to the browser.
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
        message = format_string % arguments
        print(f"[Dashboard] {message}")


# ---------------------------------------------------------
# Server startup
# ---------------------------------------------------------

def open_browser() -> None:
    """
    Open the dashboard after the server has started.
    """

    dashboard_url = f"http://{HOST}:{PORT}"

    timer = threading.Timer(
        0.5,
        webbrowser.open,
        args=(dashboard_url,),
    )

    timer.daemon = True
    timer.start()


def run_dashboard() -> None:
    """
    Start and run the local dashboard server.
    """

    server_address = (
        HOST,
        PORT,
    )

    try:
        server = ThreadingHTTPServer(
            server_address,
            DashboardRequestHandler,
        )

    except OSError as error:
        print(
            "Could not start DK Tracker dashboard "
            f"on port {PORT}."
        )
        print(error)
        return

    dashboard_url = f"http://{HOST}:{PORT}"

    print("===================================")
    print(" DK Tracker Dashboard")
    print("===================================")
    print()
    print(f"Career data: {SESSIONS_FOLDER}")
    print(f"Running at : {dashboard_url}")
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