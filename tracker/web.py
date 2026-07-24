from html import escape
from http import HTTPStatus
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path
import threading
import webbrowser

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


def load_dashboard_data() -> tuple[
    CareerSummary,
    SessionSummary,
    str,
]:
    """
    Load the career summary and most recent compatible session.
    """

    career = load_career(SESSIONS_FOLDER)
    career_summary = analyze_career(career)

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

    <meta
        http-equiv="refresh"
        content="10"
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
            <strong>Dashboard data loaded.</strong>
            This page refreshes automatically every 10 seconds.
        </div>
    </main>
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

        self.send_html(
            build_not_found_html(
                requested_path
            ),
            status=HTTPStatus.NOT_FOUND,
        )

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

    def log_message(
        self,
        format_string: str,
        *arguments: object,
    ) -> None:
        message = format_string % arguments
        print(f"[Dashboard] {message}")


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