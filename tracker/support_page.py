from __future__ import annotations

from html import escape
import json
from pathlib import Path
import platform
import re

from launcher import PROJECT_PLUGIN
from tracker.config import (
    CONFIG_FILE,
    DATA_FOLDER,
    SESSIONS_FOLDER,
    USER_DATA_FOLDER,
    load_config,
    validate_config,
)


APP_VERSION = "0.1.0"
APP_BUILD = "1"


def read_plugin_version(
    plugin_path: Path,
) -> str:
    """
    Read a declared version from the bundled Lua plugin.

    Return a neutral message when no version declaration
    can be found.
    """

    try:
        plugin_text = plugin_path.read_text(
            encoding="utf-8"
        )
    except (
        OSError,
        UnicodeDecodeError,
    ):
        return "Unavailable"

    version_match = re.search(
        (
            r"(?im)^\s*"
            r"(?:local\s+)?"
            r"(?:plugin_)?version"
            r"\s*=\s*"
            r"[\"']([^\"']+)[\"']"
        ),
        plugin_text,
    )

    if version_match is None:
        return "Not declared"

    return version_match.group(1)


def build_path_card(
    title: str,
    path: Path | None,
    unconfigured_message: str,
) -> str:
    """
    Build one diagnostic path card.
    """

    if path is None:
        status_text = "Not configured"
        status_class = "warning"
        path_text = unconfigured_message

    elif path.exists():
        status_text = "Available"
        status_class = "ok"
        path_text = str(path)

    else:
        status_text = "Missing"
        status_class = "error"
        path_text = str(path)

    return f"""
    <article class="diagnostic-card">
        <div class="diagnostic-heading">
            <h2>{escape(title)}</h2>

            <span class="status {status_class}">
                {escape(status_text)}
            </span>
        </div>

        <p class="path">
            {escape(path_text)}
        </p>
    </article>
    """


def build_support_page() -> str:
    """
    Build the read-only Support & Diagnostics page.
    """

    config = load_config()
    config_problems = validate_config(config)

    mame_executable = (
        Path(config.mame_executable)
        if config.mame_executable
        else None
    )

    rom_file = (
        Path(config.rom_file)
        if config.rom_file
        else None
    )

    installed_plugin = (
        mame_executable.parent
        / "plugins"
        / "dktracker"
        / "init.lua"
        if mame_executable is not None
        else None
    )

    operating_system_parts = [
        platform.system(),
        platform.release(),
        platform.machine(),
    ]

    operating_system = " · ".join(
        part
        for part in operating_system_parts
        if part
    )

    if not operating_system:
        operating_system = "Unknown"

    plugin_version = read_plugin_version(
        PROJECT_PLUGIN
    )

    if config_problems:
        configuration_status = (
            '<span class="status error">'
            "Needs attention"
            "</span>"
        )

        configuration_details = "".join(
            f"<li>{escape(problem)}</li>"
            for problem in config_problems
        )

        configuration_html = f"""
        <ul class="problem-list">
            {configuration_details}
        </ul>
        """

    else:
        configuration_status = (
            '<span class="status ok">'
            "Configuration valid"
            "</span>"
        )

        configuration_html = """
        <p class="configuration-ok">
            The saved MAME and ROM paths pass
            Jungle Gym's basic checks.
        </p>
        """

    path_cards = "".join(
        [
            build_path_card(
                "MAME executable",
                mame_executable,
                "No MAME executable selected.",
            ),
            build_path_card(
                "Donkey Kong ROM",
                rom_file,
                "No dkong.zip ROM selected.",
            ),
            build_path_card(
                "User data folder",
                USER_DATA_FOLDER,
                "User data folder unavailable.",
            ),
            build_path_card(
                "Career data folder",
                DATA_FOLDER,
                "Career data folder unavailable.",
            ),
            build_path_card(
                "Session folder",
                SESSIONS_FOLDER,
                "Session folder unavailable.",
            ),
            build_path_card(
                "Configuration file",
                CONFIG_FILE,
                "Configuration file unavailable.",
            ),
            build_path_card(
                "Bundled tracker plugin",
                PROJECT_PLUGIN,
                "Bundled plugin unavailable.",
            ),
            build_path_card(
                "Installed MAME plugin",
                installed_plugin,
                "MAME has not been configured.",
            ),
        ]
    )

    def format_report_path(
        path: Path | None,
    ) -> str:
        """
        Format one path for the copied report.

        Replace the user's home-folder prefix with ~
        so shared diagnostics do not expose a username.
        """

        if path is None:
            return "Not configured"

        availability = (
            "available"
            if path.exists()
            else "missing"
        )

        try:
            relative_path = path.relative_to(
                Path.home()
            )

        except ValueError:
            display_path = str(path)

        else:
            display_path = (
                "~"
                if not relative_path.parts
                else f"~/{relative_path}"
            )

        return (
            f"{display_path} "
            f"({availability})"
        )

    configuration_report = (
        ["Configuration status: Valid"]
        if not config_problems
        else [
            "Configuration status: Needs attention",
            *(
                f"Configuration problem: {problem}"
                for problem in config_problems
            ),
        ]
    )

    diagnostics_report = "\n".join(
        [
            "Jungle Gym Diagnostics",
            "======================",
            (
                f"Version: {APP_VERSION} "
                f"(Build {APP_BUILD})"
            ),
            f"Operating system: {operating_system}",
            (
                "Python runtime: "
                f"{platform.python_version()}"
            ),
            (
                "Tracker plugin version: "
                f"{plugin_version}"
            ),
            "",
            *configuration_report,
            "",
            (
                "MAME executable: "
                f"{format_report_path(mame_executable)}"
            ),
            (
                "Donkey Kong ROM: "
                f"{format_report_path(rom_file)}"
            ),
            (
                "User data folder: "
                f"{format_report_path(USER_DATA_FOLDER)}"
            ),
            (
                "Career data folder: "
                f"{format_report_path(DATA_FOLDER)}"
            ),
            (
                "Session folder: "
                f"{format_report_path(SESSIONS_FOLDER)}"
            ),
            (
                "Configuration file: "
                f"{format_report_path(CONFIG_FILE)}"
            ),
            (
                "Bundled tracker plugin: "
                f"{format_report_path(PROJECT_PLUGIN)}"
            ),
            (
                "Installed MAME plugin: "
                f"{format_report_path(installed_plugin)}"
            ),
        ]
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

    <title>Jungle Gym Support & Diagnostics</title>

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

            --primary-text: #fefcff;
            --secondary-text: #13f3ff;

            --girder-primary: #ec3193;
            --girder-highlight: #f057e8;
            --girder-shadow: #8e0305;

            --ladder-primary: #13f3ff;
            --barrel-orange: #ee7511;
            --barrel-gold: #f4ba15;

            --score-yellow: #f8f919;
            --bonus-green: #11ef11;
            --danger-red: #e80709;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            min-height: 100vh;
            margin: 0;
            padding: clamp(18px, 4vw, 42px);
            background:
                radial-gradient(
                    circle at top,
                    #120000 0,
                    var(--page-background) 420px
                );
            color: var(--primary-text);
        }}

        main {{
            position: relative;
            width: min(100%, 980px);
            margin: 0 auto;
            padding:
                clamp(30px, 5vw, 46px)
                clamp(20px, 5vw, 42px);
            overflow: hidden;
            border:
                2px solid
                var(--girder-primary);
            border-right:
                12px double
                var(--ladder-primary);
            border-left:
                12px double
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
                0 12px 34px
                rgb(0 0 0 / 0.48);
        }}

        main::before,
        main::after {{
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
        }}

        main::before {{
            top: 0;
        }}

        main::after {{
            bottom: 0;
        }}

        h1 {{
            margin: 0;
            color: var(--barrel-gold);
            font-family:
                "Courier New",
                monospace;
            font-size: clamp(2rem, 7vw, 3.8rem);
            font-weight: 900;
            line-height: 0.95;
            letter-spacing: 0.07em;
            text-align: center;
            text-shadow:
                3px 3px 0
                var(--barrel-orange);
        }}

        .subtitle {{
            margin: 12px 0 30px;
            color: var(--ladder-primary);
            font-family:
                "Courier New",
                monospace;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-align: center;
            text-transform: uppercase;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(220px, 1fr)
                );
            gap: 14px;
            margin-bottom: 18px;
        }}

        .summary-card,
        .configuration-card,
        .diagnostic-card {{
            border:
                1px solid
                var(--girder-primary);
            border-radius: 7px;
            background:
                linear-gradient(
                    180deg,
                    #0b000b,
                    var(--card-background)
                );
            box-shadow:
                inset 0 0 0 1px
                rgb(240 87 232 / 0.08),
                0 8px 22px
                rgb(0 0 0 / 0.28);
        }}

        .summary-card {{
            padding: 18px;
        }}

        .summary-label {{
            margin: 0 0 8px;
            color: var(--ladder-primary);
            font:
                700 0.78rem
                "Courier New",
                monospace;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}

        .summary-value {{
            margin: 0;
            overflow-wrap: anywhere;
            color: var(--primary-text);
            font:
                700 1rem
                "Courier New",
                monospace;
            line-height: 1.45;
        }}

        .configuration-card {{
            margin-bottom: 18px;
            padding: 20px;
        }}

        .configuration-heading,
        .diagnostic-heading {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }}

        h2 {{
            margin: 0;
            color: var(--barrel-gold);
            font:
                900 1rem
                "Courier New",
                monospace;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}

        .status {{
            flex: 0 0 auto;
            padding: 5px 8px;
            border: 1px solid currentColor;
            border-radius: 999px;
            font:
                700 0.72rem
                "Courier New",
                monospace;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }}

        .status.ok {{
            color: var(--bonus-green);
        }}

        .status.warning {{
            color: var(--score-yellow);
        }}

        .status.error {{
            color: var(--danger-red);
        }}

        .configuration-ok {{
            margin: 16px 0 0;
            color: var(--ladder-primary);
            line-height: 1.55;
        }}

        .problem-list {{
            margin: 16px 0 0;
            padding-left: 22px;
            color: var(--danger-red);
            line-height: 1.55;
        }}

        .diagnostic-grid {{
            display: grid;
            gap: 14px;
        }}

        .diagnostic-card {{
            padding: 18px;
        }}

        .path {{
            margin: 13px 0 0;
            overflow-wrap: anywhere;
            color: var(--ladder-primary);
            font:
                0.84rem/1.55
                "Courier New",
                monospace;
        }}

        .support-actions {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 12px;
            margin-top: 28px;
        }}

        .support-action,
        .back-link {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 11px 16px;
            border:
                1px solid
                var(--score-yellow);
            border-radius: 7px;
            background: var(--card-background);
            color: var(--barrel-gold);
            font:
                900 0.9rem
                "Courier New",
                monospace;
            letter-spacing: 0.03em;
            text-decoration: none;
        }}

        .support-action {{
            appearance: none;
            border-color: var(--ladder-primary);
            color: var(--ladder-primary);
            cursor: pointer;
        }}

        .support-action:hover:not(:disabled),
        .back-link:hover {{
            background: #180018;
            border-color: var(--score-yellow);
            color: var(--score-yellow);
        }}

        .support-action:disabled {{
            cursor: wait;
            opacity: 0.55;
        }}

        .support-action:focus-visible,
        .back-link:focus-visible {{
            outline:
                2px solid
                var(--ladder-primary);
            outline-offset: 3px;
        }}

        .copy-status {{
            min-height: 22px;
            margin: 13px 0 0;
            color: var(--ladder-primary);
            font:
                700 0.78rem/1.4
                "Courier New",
                monospace;
            text-align: center;
        }}
    </style>
</head>

<body>
    <main>
        <h1>JUNGLE GYM</h1>

        <p class="subtitle">
            Support &amp; Diagnostics
        </p>

        <section class="summary-grid">
            <article class="summary-card">
                <p class="summary-label">
                    Jungle Gym version
                </p>

                <p class="summary-value">
                    {escape(APP_VERSION)}
                    (Build {escape(APP_BUILD)})
                </p>
            </article>

            <article class="summary-card">
                <p class="summary-label">
                    Operating system
                </p>

                <p class="summary-value">
                    {escape(operating_system)}
                </p>
            </article>

            <article class="summary-card">
                <p class="summary-label">
                    Python runtime
                </p>

                <p class="summary-value">
                    {escape(platform.python_version())}
                </p>
            </article>

            <article class="summary-card">
                <p class="summary-label">
                    Tracker plugin version
                </p>

                <p class="summary-value">
                    {escape(plugin_version)}
                </p>
            </article>
        </section>

        <section class="configuration-card">
            <div class="configuration-heading">
                <h2>Configuration</h2>

                {configuration_status}
            </div>

            {configuration_html}
        </section>

        <section class="diagnostic-grid">
            {path_cards}
        </section>

        <div class="support-actions">
            <a
                class="support-action"
                href="/support/open-data"
            >
                Open Data Folder
            </a>

            <button
                id="copy-diagnostics-button"
                class="support-action"
                type="button"
            >
                Copy Diagnostics
            </button>

            <a class="back-link" href="/">
                Back to Dashboard
            </a>
        </div>

        <p
            id="copy-diagnostics-status"
            class="copy-status"
            aria-live="polite"
        ></p>
    </main>

    <script>
        const copyDiagnosticsButton =
            document.getElementById(
                "copy-diagnostics-button"
            );

        const copyDiagnosticsStatus =
            document.getElementById(
                "copy-diagnostics-status"
            );

        const diagnosticsReport =
            {json.dumps(diagnostics_report)};

        async function copyDiagnostics() {{
            copyDiagnosticsButton.disabled = true;

            copyDiagnosticsStatus.textContent =
                "Copying diagnostics...";

            try {{
                if (
                    navigator.clipboard
                    && window.isSecureContext
                ) {{
                    await navigator.clipboard.writeText(
                        diagnosticsReport
                    );
                }} else {{
                    const textArea =
                        document.createElement(
                            "textarea"
                        );

                    textArea.value =
                        diagnosticsReport;

                    textArea.setAttribute(
                        "readonly",
                        ""
                    );

                    textArea.style.position =
                        "fixed";

                    textArea.style.opacity =
                        "0";

                    document.body.appendChild(
                        textArea
                    );

                    textArea.focus();
                    textArea.select();

                    textArea.setSelectionRange(
                        0,
                        textArea.value.length
                    );

                    const copySucceeded =
                        document.execCommand(
                            "copy"
                        );

                    textArea.remove();

                    if (!copySucceeded) {{
                        throw new Error(
                            "Clipboard copy failed."
                        );
                    }}
                }}

                copyDiagnosticsStatus.textContent = (
                    "Diagnostics copied. "
                    + "Review paths before sharing."
                );

            }} catch (error) {{
                copyDiagnosticsStatus.textContent = (
                    "Copy failed. Try copying "
                    + "the displayed details manually."
                );

            }} finally {{
                copyDiagnosticsButton.disabled =
                    false;
            }}
        }}

        copyDiagnosticsButton.addEventListener(
            "click",
            copyDiagnostics
        );
    </script>
</body>
</html>
"""


__all__ = [
    "build_support_page",
]
