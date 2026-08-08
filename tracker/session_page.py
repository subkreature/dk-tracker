from __future__ import annotations

from html import escape
import json
from string import Template
from typing import Any


def build_session_page(
    session_name: str,
    session_detail: dict[str, Any],
    session_names: list[str],
) -> str:
    """
    Build the completed-session details page.
    """

    duration_seconds = int(
        session_detail["duration_seconds"]
    )

    duration_minutes, duration_remainder = divmod(
        duration_seconds,
        60,
    )

    overall_score_pb = session_detail.get(
        "personal_bests",
        {},
    ).get(
        "overall_score",
        {},
    )

    career_best = int(
        overall_score_pb.get(
            "career_best",
            session_detail["final_score"],
        )
    )

    is_personal_best = bool(
        overall_score_pb.get("is_pb", False)
    )

    if is_personal_best:
        achievement_class = "personal-best"
        achievement_label = "🏆 Personal Best"
        achievement_detail = "New career-high score"
    else:
        achievement_class = "career-best"
        achievement_label = "Career Best"
        achievement_detail = f"{career_best:,} points"

    score_points_json = json.dumps(
        session_detail["score_points"]
    ).replace("<", "\\u003c")

    events_json = json.dumps(
        session_detail["events"]
    ).replace("<", "\\u003c")

    board_split_rows: list[str] = []

    for split in session_detail.get("board_splits", []):
        split_seconds = int(round(float(split.get("duration_seconds", 0.0))))
        split_minutes, split_remainder = divmod(split_seconds, 60)

        completed = bool(split.get("completed", False))
        status_label = "Cleared" if completed else "Incomplete"
        status_class = "complete" if completed else "incomplete"

        score_gained = split.get("score_gained")
        score_text = (
            f"{int(score_gained):,}"
            if score_gained is not None
            else "--"
        )

        screen_name = str(
            split.get("screen_name", "") or "Unknown"
        ).replace("_", " ").title()

        board_split_rows.append(
            "<tr>"
            f'<td class="split-board">'
            f'{escape(str(split.get("board", "Unknown")))}</td>'
            f"<td>{escape(screen_name)}</td>"
            f"<td>{split_minutes}:{split_remainder:02d}</td>"
            f"<td>{score_text}</td>"
            f'<td><span class="split-status {status_class}">'
            f"{status_label}</span></td>"
            "</tr>"
        )

    if board_split_rows:
        board_splits_content = """
            <div class="split-table-wrap">
                <table class="split-table">
                    <thead>
                        <tr>
                            <th>Board</th>
                            <th>Screen</th>
                            <th>Time</th>
                            <th>Score Gained</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        """ + "\n".join(board_split_rows) + """
                    </tbody>
                </table>
            </div>
        """
    else:
        board_splits_content = """
            <p class="split-empty">
                No board timing data is available for this session.
            </p>
        """

    session_options = "\n".join(
        (
            '<option value="'
            + escape(name, quote=True)
            + '"'
            + (
                " selected"
                if name == session_name
                else ""
            )
            + ">"
            + escape(name.replace("_", " "))
            + "</option>"
        )
        for name in session_names
    )

    page_template = Template(
        """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>Session Details</title>

    <style>
        :root {
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
        }

        * {
            box-sizing: border-box;
        }

        body {
            min-height: 100vh;
            margin: 0;
            padding: clamp(18px, 4vw, 40px);
            background:
                radial-gradient(
                    circle at top,
                    #120000 0,
                    var(--page-background) 360px
                );
            color: var(--primary-text);
        }

        main {
            width: min(100%, 1100px);
            margin: 0 auto;
        }

        header {
            position: relative;
            margin-bottom: 32px;
            padding:
                clamp(24px, 4vw, 38px)
                clamp(18px, 4vw, 34px);
            overflow: hidden;
            border:
                2px solid
                var(--girder-primary);
            border-right:
                14px double
                var(--ladder-primary);
            border-left:
                14px double
                var(--ladder-primary);
            border-radius: 8px;
            background:
                linear-gradient(
                    180deg,
                    #080008,
                    var(--panel-background)
                );
            box-shadow:
                0 0 0 3px
                var(--girder-shadow),
                0 10px 30px
                rgb(0 0 0 / 0.45);
            text-align: center;
        }

        header::before,
        header::after {
            content: "";
            position: absolute;
            right: 0;
            left: 0;
            height: 8px;
            background:
                repeating-linear-gradient(
                    135deg,
                    var(--girder-highlight) 0 8px,
                    var(--girder-primary) 8px 16px,
                    var(--girder-shadow) 16px 24px
                );
        }

        header::before {
            top: 0;
        }

        header::after {
            bottom: 0;
        }

        h1 {
            margin: 0 0 12px;
            color: var(--barrel-gold);
            font-family:
                "Courier New",
                monospace;
            font-size: clamp(
                2.2rem,
                7vw,
                4.5rem
            );
            font-weight: 900;
            line-height: 0.95;
            letter-spacing: 0.08em;
            text-shadow:
                3px 3px 0
                var(--barrel-orange),
                0 0 18px
                rgb(244 186 21 / 0.26);
        }

        .session-name {
            margin: 0;
            color: var(--secondary-text);
            font-family: monospace;
        }

        .session-selector {
            width: min(100%, 420px);
            margin: 20px auto 0;
            text-align: left;
        }

        .session-selector label {
            display: block;
            margin-bottom: 8px;
            color: var(--secondary-text);
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .session-selector select {
            width: 100%;
            padding: 12px 14px;
            border: 1px solid var(--card-border);
            border-radius: 10px;
            background: var(--card-background);
            color: var(--primary-text);
            font: inherit;
            cursor: pointer;
        }

        .session-selector select:focus {
            border-color: var(--accent);
            outline: 2px solid rgba(232, 184, 74, 0.22);
            outline-offset: 2px;
        }

        .achievement-banner {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 24px;
            padding: 20px 24px;
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
                0 0 0 3px
                var(--girder-shadow),
                0 10px 24px
                rgb(0 0 0 / 0.38);
        }

        .achievement-banner::before {
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            left: 0;
            height: 6px;
            background:
                repeating-linear-gradient(
                    135deg,
                    var(--girder-highlight) 0 6px,
                    var(--girder-primary) 6px 12px,
                    var(--girder-shadow) 12px 18px
                );
        }

        .achievement-banner.personal-best {
            border-color: var(--score-yellow);
            background:
                linear-gradient(
                    135deg,
                    rgb(244 186 21 / 0.12),
                    var(--panel-background)
                );
            box-shadow:
                0 0 0 3px
                var(--barrel-orange),
                0 10px 24px
                rgb(0 0 0 / 0.38);
        }

        .achievement-label {
            margin: 0;
            color: var(--barrel-gold);
            font-family:
                "Courier New",
                monospace;
            font-size: 1rem;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .achievement-banner.personal-best
        .achievement-label {
            color: var(--score-yellow);
            text-shadow:
                1px 1px 0
                var(--barrel-orange);
        }

        .achievement-detail {
            margin: 5px 0 0;
            color: var(--ladder-primary);
        }

        .achievement-score {
            flex: 0 0 auto;
            color: var(--score-yellow);
            font-family:
                "Courier New",
                monospace;
            font-size: clamp(1.7rem, 5vw, 2.4rem);
            font-weight: 900;
            text-shadow:
                2px 2px 0
                var(--barrel-orange);
        }

        .summary-grid {
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(180px, 1fr)
                );
            gap: 16px;
            margin-bottom: 32px;
        }

        .summary-card {
            position: relative;
            min-height: 130px;
            padding: 24px 22px 22px;
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
                rgb(240 87 232 / 0.1),
                0 8px 22px
                rgb(0 0 0 / 0.34);
        }

        .summary-card::before {
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            left: 0;
            height: 5px;
            background:
                repeating-linear-gradient(
                    135deg,
                    var(--girder-highlight) 0 6px,
                    var(--girder-primary) 6px 12px,
                    var(--girder-shadow) 12px 18px
                );
        }

        .summary-label {
            margin: 0 0 14px;
            color: var(--ladder-primary);
            font-family:
                "Courier New",
                monospace;
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .summary-value {
            margin: 0;
            color: var(--primary-text);
            font-family:
                "Courier New",
                monospace;
            font-size: 2rem;
            font-weight: 900;
            text-shadow:
                1px 1px 0
                var(--girder-shadow);
        }

        .summary-card.primary {
            border-color: var(--score-yellow);
            box-shadow:
                inset 0 0 0 1px
                rgb(248 249 25 / 0.12),
                0 8px 22px
                rgb(0 0 0 / 0.34);
        }

        .summary-card.primary::before {
            background:
                repeating-linear-gradient(
                    135deg,
                    var(--score-yellow) 0 6px,
                    var(--barrel-gold) 6px 12px,
                    var(--barrel-orange) 12px 18px
                );
        }

        .summary-card.primary .summary-value {
            color: var(--score-yellow);
            font-size: 2.5rem;
            text-shadow:
                2px 2px 0
                var(--barrel-orange);
        }

        .splits-panel {
            position: relative;
            margin-bottom: 32px;
            padding: 28px 24px 24px;
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
                0 0 0 3px
                var(--girder-shadow),
                0 10px 28px
                rgb(0 0 0 / 0.4);
        }

        .splits-panel::before,
        .splits-panel::after {
            content: "";
            position: absolute;
            right: 0;
            left: 0;
            height: 7px;
            background:
                repeating-linear-gradient(
                    135deg,
                    var(--girder-highlight) 0 7px,
                    var(--girder-primary) 7px 14px,
                    var(--girder-shadow) 14px 21px
                );
        }

        .splits-panel::before {
            top: 0;
        }

        .splits-panel::after {
            bottom: 0;
        }

        .splits-panel h2 {
            margin: 0;
            color: var(--barrel-gold);
            font-family:
                "Courier New",
                monospace;
            font-size: 1.35rem;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            text-shadow:
                1px 1px 0
                var(--barrel-orange);
        }

        .splits-description {
            margin: 8px 0 20px;
            color: var(--ladder-primary);
        }

        .split-table-wrap {
            overflow-x: auto;
            border:
                1px solid
                rgb(19 243 255 / 0.24);
            border-radius: 6px;
            background: #030003;
        }

        .split-table {
            width: 100%;
            border-collapse: collapse;
        }

        .split-table th,
        .split-table td {
            padding: 13px 12px;
            border-bottom:
                1px solid
                rgb(236 49 147 / 0.32);
            text-align: left;
            white-space: nowrap;
        }

        .split-table th {
            background:
                linear-gradient(
                    180deg,
                    #0d000d,
                    #060006
                );
            color: var(--ladder-primary);
            font-family:
                "Courier New",
                monospace;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.07em;
            text-transform: uppercase;
        }

        .split-table tbody tr {
            transition:
                background 120ms ease,
                box-shadow 120ms ease;
        }

        .split-table tbody tr:hover {
            background:
                rgb(236 49 147 / 0.08);
            box-shadow:
                inset 4px 0 0
                var(--girder-primary);
        }

        .split-table tbody tr:last-child td {
            border-bottom: 0;
        }

        .split-board {
            color: var(--score-yellow);
            font-family:
                "Courier New",
                monospace;
            font-size: 1.05rem;
            font-weight: 900;
            text-shadow:
                1px 1px 0
                var(--barrel-orange);
        }

        .split-status {
            display: inline-block;
            padding: 5px 9px;
            border: 1px solid currentColor;
            border-radius: 4px;
            font-family:
                "Courier New",
                monospace;
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .split-status.complete {
            background:
                rgb(17 239 17 / 0.1);
            color: var(--bonus-green);
        }

        .split-status.incomplete {
            background:
                rgb(232 7 9 / 0.1);
            color: var(--danger-red);
        }

        .split-empty {
            margin: 18px 0 0;
            color: var(--ladder-primary);
        }

        .chart-panel {
            position: relative;
            margin-bottom: 32px;
            padding: 28px 24px 24px;
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
                0 0 0 3px
                var(--girder-shadow),
                0 10px 28px
                rgb(0 0 0 / 0.4);
        }

        .chart-panel::before,
        .chart-panel::after {
            content: "";
            position: absolute;
            right: 0;
            left: 0;
            height: 7px;
            background:
                repeating-linear-gradient(
                    135deg,
                    var(--girder-highlight) 0 7px,
                    var(--girder-primary) 7px 14px,
                    var(--girder-shadow) 14px 21px
                );
        }

        .chart-panel::before {
            top: 0;
        }

        .chart-panel::after {
            bottom: 0;
        }

        .chart-panel h2 {
            margin: 0 0 20px;
            color: var(--barrel-gold);
            font-family:
                "Courier New",
                monospace;
            font-size: 1.35rem;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            text-shadow:
                1px 1px 0
                var(--barrel-orange);
        }

        .chart-container {
            position: relative;
            min-height: 360px;
            padding: 12px;
            border:
                1px solid
                rgb(19 243 255 / 0.22);
            border-radius: 6px;
            background:
                linear-gradient(
                    180deg,
                    #050005,
                    #000000
                );
            box-shadow:
                inset 0 0 24px
                rgb(3 1 220 / 0.1);
        }

        .event-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 10px 12px;
            margin-top: 18px;
            color: var(--ladder-primary);
            font-size: 0.85rem;
        }

        .event-legend-item {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 10px;
            border:
                1px solid
                rgb(19 243 255 / 0.22);
            border-radius: 5px;
            background: #050005;
            color: var(--ladder-primary);
            font: inherit;
            cursor: pointer;
            transition:
                border-color 120ms ease,
                background 120ms ease,
                color 120ms ease;
        }

        .event-legend-item:hover {
            border-color: var(--score-yellow);
            background: var(--button-hover);
            color: var(--score-yellow);
        }

        .event-legend-item[aria-pressed="false"] {
            opacity: 0.42;
        }

        .event-legend-item[aria-pressed="false"]
        .event-legend-marker {
            filter: grayscale(1);
        }

        .event-legend-marker {
            display: inline-flex;
            min-width: 24px;
            height: 24px;
            align-items: center;
            justify-content: center;
            border:
                1px solid
                currentColor;
            border-radius: 4px;
            color: #000000;
            font-family:
                "Courier New",
                monospace;
            font-size: 0.72rem;
            font-weight: 900;
            line-height: 1;
            box-shadow:
                inset 0 0 0 1px
                rgb(255 255 255 / 0.12);
        }

        .event-legend-marker.life-lost {
            background: var(--danger-red);
        }

        .event-legend-marker.bonus-life {
            background: var(--bonus-green);
        }

        .event-legend-marker.game-start {
            background: var(--ladder-primary);
        }

        .event-legend-marker.board-transition {
            background: var(--score-yellow);
        }

        .dashboard-link {
            display: inline-block;
            padding: 12px 18px;
            border:
                1px solid
                var(--score-yellow);
            border-radius: 6px;
            background: var(--card-background);
            color: var(--barrel-gold);
            font-family:
                "Courier New",
                monospace;
            font-weight: 700;
            text-decoration: none;
        }

        .dashboard-link:hover {
            background: var(--button-hover);
            color: var(--score-yellow);
        }

        @media (max-width: 600px) {
            body {
                padding: 20px;
            }

            .achievement-banner {
                align-items: flex-start;
                flex-direction: column;
            }

            .summary-grid {
                grid-template-columns: 1fr 1fr;
            }

            .chart-container {
                min-height: 300px;
            }
        }
    </style>
</head>
<body>
    <main>
        <header>
            <h1>Session Details</h1>

            <p class="session-name">
                $session_name
            </p>

            <div class="session-selector">
                <label for="session-select">
                    Session history
                </label>

                <select id="session-select">
                    $session_options
                </select>
            </div>
        </header>

        <section
            class="achievement-banner $achievement_class"
            aria-label="Career score achievement"
        >
            <div>
                <p class="achievement-label">
                    $achievement_label
                </p>

                <p class="achievement-detail">
                    $achievement_detail
                </p>
            </div>

            <div class="achievement-score">
                $career_best
            </div>
        </section>

        <section
            class="summary-grid"
            aria-label="Session summary"
        >
            <article class="summary-card primary">
                <p class="summary-label">
                    Final Score
                </p>

                <p class="summary-value">
                    $final_score
                </p>
            </article>

            <article class="summary-card">
                <p class="summary-label">
                    Duration
                </p>

                <p class="summary-value">
                    $duration
                </p>
            </article>

            <article class="summary-card">
                <p class="summary-label">
                    Highest Board
                </p>

                <p class="summary-value">
                    $highest_board
                </p>
            </article>

            <article class="summary-card">
                <p class="summary-label">
                    Lives Lost
                </p>

                <p class="summary-value">
                    $lives_lost
                </p>
            </article>

            <article class="summary-card">
                <p class="summary-label">
                    Bonus Lives
                </p>

                <p class="summary-value">
                    $bonus_lives
                </p>
            </article>

            <article class="summary-card">
                <p class="summary-label">
                    Boards Cleared
                </p>

                <p class="summary-value">
                    $boards_cleared
                </p>
            </article>
        </section>

        <section class="splits-panel">
            <h2>Board Splits</h2>

            <p class="splits-description">
                Time and score gained on each board in this session.
            </p>

            $board_splits_content
        </section>

        <section class="chart-panel">
            <h2>Score Progression</h2>

            <div class="chart-container">
                <canvas id="score-chart"></canvas>
            </div>

            <div
                class="event-legend"
                aria-label="Graph marker controls"
            >
                <button
                    class="event-legend-item"
                    type="button"
                    data-marker-toggle="board_transition"
                    aria-pressed="true"
                >
                    <span
                        class="event-legend-marker board-transition"
                    >
                        B
                    </span>
                    Boards
                </button>

                <button
                    class="event-legend-item"
                    type="button"
                    data-marker-toggle="life_lost"
                    aria-pressed="true"
                >
                    <span class="event-legend-marker life-lost">
                        L
                    </span>
                    Life lost
                </button>

                <button
                    class="event-legend-item"
                    type="button"
                    data-marker-toggle="bonus_life"
                    aria-pressed="true"
                >
                    <span class="event-legend-marker bonus-life">
                        1UP
                    </span>
                    Bonus life
                </button>

                <button
                    class="event-legend-item"
                    type="button"
                    data-marker-toggle="game_start"
                    aria-pressed="true"
                >
                    <span class="event-legend-marker game-start">
                        GO
                    </span>
                    Game start
                </button>
            </div>
        </section>

        <a
            class="dashboard-link"
            href="/"
        >
            Return to dashboard
        </a>
    </main>

    <script
        src="/static/chart.umd.min.js"
    ></script>

    <script>
        const SCORE_POINTS = $score_points_json;
        const EVENTS = $events_json;

        const sessionSelect = document.getElementById(
            "session-select"
        );

        sessionSelect.addEventListener(
            "change",
            () => {
                const selectedName = sessionSelect.value;
                window.location.href = (
                    "/session?name="
                    + encodeURIComponent(selectedName)
                );
            }
        );

        function formatElapsedTime(seconds) {
            const wholeSeconds = Math.floor(seconds);
            const minutes = Math.floor(
                wholeSeconds / 60
            );
            const remainder = wholeSeconds % 60;

            return (
                String(minutes)
                + ":"
                + String(remainder).padStart(2, "0")
            );
        }

        const chartCanvas = document.getElementById(
            "score-chart"
        );

        const chartData = SCORE_POINTS.map(
            (point) => ({
                x: point.elapsed_seconds,
                y: point.score,
            })
        );

        const BOARD_TRANSITIONS = EVENTS.filter(
            (event) => (
                event.event === "level_transition"
                && Number.isFinite(event.elapsed_seconds)
            )
        );

        const EVENT_MARKER_STYLES = {
            life_lost: {
                label: "L",
                fill: "#ef6a6a",
                text: "#101218",
                lane: 0,
            },
            bonus_life: {
                label: "1UP",
                fill: "#71d58a",
                text: "#101218",
                lane: 1,
            },
            game_start: {
                label: "GO",
                fill: "#6fa8ff",
                text: "#101218",
                lane: 2,
            },
        };

        const EVENT_NAME_ALIASES = {
            life_lost: "life_lost",
            lives_lost: "life_lost",
            bonus_life: "bonus_life",
            bonus_life_earned: "bonus_life",
            extra_life: "bonus_life",
            game_start: "game_start",
            game_started: "game_start",
            new_game: "game_start",
        };

        const GAMEPLAY_MARKERS = EVENTS
            .map((event) => {
                const canonicalName = EVENT_NAME_ALIASES[
                    event.event
                ];

                if (
                    !canonicalName
                    || !Number.isFinite(event.elapsed_seconds)
                ) {
                    return null;
                }

                return {
                    ...event,
                    canonicalName,
                    markerStyle:
                        EVENT_MARKER_STYLES[canonicalName],
                };
            })
            .filter((event) => event !== null);

        const markerVisibility = {
            board_transition: true,
            life_lost: true,
            bonus_life: true,
            game_start: true,
        };

        const markerToggleButtons = document.querySelectorAll(
            "[data-marker-toggle]"
        );

        let scoreChart = null;

        markerToggleButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const markerType = button.dataset.markerToggle;
                markerVisibility[markerType] = (
                    !markerVisibility[markerType]
                );

                button.setAttribute(
                    "aria-pressed",
                    String(markerVisibility[markerType])
                );

                if (scoreChart !== null) {
                    scoreChart.draw();
                }
            });
        });

        const boardTransitionPlugin = {
            id: "boardTransitionMarkers",

            afterDatasetsDraw(chart) {
                if (
                    !markerVisibility.board_transition
                    || BOARD_TRANSITIONS.length === 0
                ) {
                    return;
                }

                const {
                    ctx,
                    chartArea,
                    scales,
                } = chart;

                ctx.save();
                ctx.lineWidth = 1;
                ctx.setLineDash([6, 5]);
                ctx.strokeStyle = "rgba(247, 248, 250, 0.45)";
                ctx.fillStyle = "#f7f8fa";
                ctx.font = "700 12px system-ui";
                ctx.textAlign = "center";
                ctx.textBaseline = "top";

                BOARD_TRANSITIONS.forEach((event) => {
                    const xPosition = scales.x.getPixelForValue(
                        event.elapsed_seconds
                    );

                    if (
                        xPosition < chartArea.left
                        || xPosition > chartArea.right
                    ) {
                        return;
                    }

                    ctx.beginPath();
                    ctx.moveTo(xPosition, chartArea.top);
                    ctx.lineTo(xPosition, chartArea.bottom);
                    ctx.stroke();

                    const label = event.board || "Unknown";
                    const labelWidth = ctx.measureText(label).width;
                    const padding = 5;
                    const boxWidth = labelWidth + (padding * 2);
                    const boxHeight = 22;
                    const boxLeft = Math.min(
                        Math.max(
                            xPosition - (boxWidth / 2),
                            chartArea.left
                        ),
                        chartArea.right - boxWidth
                    );
                    const boxTop = chartArea.top + 6;

                    ctx.setLineDash([]);
                    ctx.fillStyle = "rgba(16, 18, 24, 0.88)";
                    ctx.fillRect(
                        boxLeft,
                        boxTop,
                        boxWidth,
                        boxHeight
                    );

                    ctx.fillStyle = "#f7f8fa";
                    ctx.fillText(
                        label,
                        boxLeft + (boxWidth / 2),
                        boxTop + 4
                    );

                    ctx.setLineDash([6, 5]);
                    ctx.fillStyle = "#f7f8fa";
                });

                ctx.restore();
            },
        };

        const gameplayEventPlugin = {
            id: "gameplayEventMarkers",

            afterDatasetsDraw(chart) {
                if (GAMEPLAY_MARKERS.length === 0) {
                    return;
                }

                const {
                    ctx,
                    chartArea,
                    scales,
                } = chart;

                const markerHeight = 22;
                const markerGap = 5;
                const markerBottom = chartArea.bottom - 8;

                ctx.save();
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.font = "900 10px system-ui";

                GAMEPLAY_MARKERS.forEach((event) => {
                    if (!markerVisibility[event.canonicalName]) {
                        return;
                    }

                    const style = event.markerStyle;
                    const xPosition = scales.x.getPixelForValue(
                        event.elapsed_seconds
                    );

                    if (
                        xPosition < chartArea.left
                        || xPosition > chartArea.right
                    ) {
                        return;
                    }

                    const markerY = (
                        markerBottom
                        - (
                            style.lane
                            * (markerHeight + markerGap)
                        )
                    );

                    ctx.beginPath();
                    ctx.setLineDash([3, 4]);
                    ctx.lineWidth = 1;
                    ctx.strokeStyle = style.fill;
                    ctx.moveTo(xPosition, markerY - 12);
                    ctx.lineTo(xPosition, chartArea.top);
                    ctx.stroke();

                    const labelWidth = ctx.measureText(
                        style.label
                    ).width;
                    const markerWidth = Math.max(
                        markerHeight,
                        labelWidth + 12
                    );
                    const markerLeft = Math.min(
                        Math.max(
                            xPosition - (markerWidth / 2),
                            chartArea.left
                        ),
                        chartArea.right - markerWidth
                    );

                    ctx.setLineDash([]);
                    ctx.fillStyle = style.fill;
                    ctx.beginPath();
                    ctx.roundRect(
                        markerLeft,
                        markerY - (markerHeight / 2),
                        markerWidth,
                        markerHeight,
                        markerHeight / 2
                    );
                    ctx.fill();

                    ctx.fillStyle = style.text;
                    ctx.fillText(
                        style.label,
                        markerLeft + (markerWidth / 2),
                        markerY
                    );
                });

                ctx.restore();
            },
        };


        scoreChart = new Chart(
            chartCanvas,
            {
                type: "line",
                plugins: [
                    boardTransitionPlugin,
                    gameplayEventPlugin,
                ],

                data: {
                    datasets: [
                        {
                            label: "Score",
                            data: chartData,
                            borderColor: "#f8f919",
                            backgroundColor:
                                "rgba(244, 186, 21, 0.10)",
                            borderWidth: 3,
                            pointRadius: 0,
                            pointHoverRadius: 5,
                            pointHoverBackgroundColor:
                                "#f4ba15",
                            pointHoverBorderColor:
                                "#ee7511",
                            fill: true,
                            tension: 0.15,
                        },
                    ],
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    interaction: {
                        intersect: false,
                        mode: "nearest",
                    },

                    plugins: {
                        legend: {
                            display: false,
                        },

                        tooltip: {
                            callbacks: {
                                title(items) {
                                    const seconds =
                                        items[0].parsed.x;

                                    return formatElapsedTime(
                                        seconds
                                    );
                                },

                                label(item) {
                                    return (
                                        "Score: "
                                        + item.parsed.y
                                            .toLocaleString()
                                    );
                                },
                            },
                        },
                    },

                    scales: {
                        x: {
                            type: "linear",

                            title: {
                                display: true,
                                text: "Elapsed Time",
                                color:
                                    "rgba(19, 243, 255, 0.72)",
                                font: {
                                    family: "Courier New",
                                    weight: "700",
                                },
                            },

                            ticks: {
                                color:
                                    "rgba(19, 243, 255, 0.62)",

                                callback(value) {
                                    return formatElapsedTime(
                                        value
                                    );
                                },
                            },

                            grid: {
                                color:
                                    "rgba(19, 243, 255, 0.10)",
                            },
                        },

                        y: {
                            beginAtZero: true,

                            title: {
                                display: true,
                                text: "Score",
                                color:
                                    "rgba(19, 243, 255, 0.72)",
                                font: {
                                    family: "Courier New",
                                    weight: "700",
                                },
                            },

                            ticks: {
                                color:
                                    "rgba(19, 243, 255, 0.62)",

                                callback(value) {
                                    return Number(
                                        value
                                    ).toLocaleString();
                                },
                            },

                            grid: {
                                color:
                                    "rgba(19, 243, 255, 0.10)",
                            },
                        },
                    },
                },
            }
        );
    </script>
</body>
</html>
"""
    )

    return page_template.substitute(
        session_name=escape(session_name),
        achievement_class=achievement_class,
        achievement_label=escape(achievement_label),
        achievement_detail=escape(achievement_detail),
        career_best=f"{career_best:,}",
        final_score=f'{session_detail["final_score"]:,}',
        duration=(
            f"{duration_minutes}:"
            f"{duration_remainder:02d}"
        ),
        highest_board=escape(
            str(session_detail["highest_board"])
        ),
        lives_lost=session_detail["lives_lost"],
        bonus_lives=session_detail["bonus_lives"],
        boards_cleared=(
            session_detail["boards_cleared"]
        ),
        score_points_json=score_points_json,
        events_json=events_json,
        session_options=session_options,
        board_splits_content=board_splits_content,
    )