from __future__ import annotations

from html import escape


def build_setup_page(
    problems: list[str],
) -> str:
    """
    Build the first-run configuration page.
    """

    problem_items = "\n".join(
        f"<li>{escape(problem)}</li>"
        for problem in problems
    )

    if not problem_items:
        problem_items = (
            "<li>No configuration problems detected.</li>"
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

    <title>DK Tracker Setup</title>

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
            --danger: #ef7b7b;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            min-height: 100vh;
            margin: 0;
            padding: 32px;
            display: grid;
            place-items: center;
            background: var(--page-background);
            color: var(--primary-text);
        }}

        main {{
            width: min(100%, 720px);
            padding: 32px;
            border: 1px solid var(--card-border);
            border-radius: 16px;
            background: var(--panel-background);
        }}

        h1 {{
            margin: 0;
            color: var(--accent);
            font-size: clamp(2rem, 7vw, 3.5rem);
            letter-spacing: 0.06em;
            text-align: center;
        }}

        .subtitle {{
            margin: 10px 0 28px;
            color: var(--secondary-text);
            text-align: center;
        }}

        .notice {{
            padding: 20px;
            border: 1px solid var(--card-border);
            border-radius: 12px;
            background: var(--card-background);
        }}

        .notice h2 {{
            margin-top: 0;
            font-size: 1.15rem;
        }}

        .problems {{
            margin-bottom: 0;
            padding-left: 22px;
            color: var(--danger);
        }}

        .instructions {{
            margin: 24px 0 0;
            color: var(--secondary-text);
            line-height: 1.6;
        }}
    </style>
</head>

<body>
    <main>
        <h1>DK TRACKER</h1>

        <p class="subtitle">
            First-run setup
        </p>

        <section class="notice">
            <h2>Configuration required</h2>

            <ul class="problems">
                {problem_items}
            </ul>
        </section>

        <p class="instructions">
            DK Tracker needs the location of your MAME
            executable and your existing
            <strong>dkong.zip</strong> ROM before it can
            launch Donkey Kong.
        </p>

        <button
            id="choose-mame-button"
            type="button"
            style="
                width: 100%;
                margin-top: 24px;
                padding: 14px 18px;
                border: 1px solid var(--accent);
                border-radius: 10px;
                background: var(--card-background);
                color: var(--accent);
                cursor: pointer;
                font: inherit;
                font-weight: 700;
            "
        >
            Choose MAME Executable…
        </button>

        <p
            id="mame-path"
            style="
                margin: 14px 0 0;
                color: var(--secondary-text);
                overflow-wrap: anywhere;
            "
        >
            No MAME executable selected.
        </p>

        <button
            id="choose-rom-button"
            type="button"
            style="
                width: 100%;
                margin-top: 24px;
                padding: 14px 18px;
                border: 1px solid var(--accent);
                border-radius: 10px;
                background: var(--card-background);
                color: var(--accent);
                cursor: pointer;
                font: inherit;
                font-weight: 700;
            "
        >
            Choose dkong.zip…
        </button>

        <p
            id="rom-path"
            style="
                margin: 14px 0 0;
                color: var(--secondary-text);
                overflow-wrap: anywhere;
            "
        >
            No Donkey Kong ROM selected.
        </p>

        <button
            id="save-setup-button"
            type="button"
            disabled
            style="
                width: 100%;
                margin-top: 28px;
                padding: 14px 18px;
                border: 0;
                border-radius: 10px;
                background: var(--accent);
                color: #111111;
                cursor: pointer;
                font: inherit;
                font-weight: 800;
            "
        >
            Save and Continue
        </button>

        <p
            id="setup-status"
            style="
                min-height: 24px;
                margin: 14px 0 0;
                color: var(--secondary-text);
                overflow-wrap: anywhere;
            "
        ></p>
    </main>

    <script>
        const chooseMameButton =
            document.getElementById(
                "choose-mame-button"
            );

        const mamePath =
            document.getElementById(
                "mame-path"
            );

        const chooseRomButton =
            document.getElementById(
                "choose-rom-button"
            );

        const romPath =
            document.getElementById(
                "rom-path"
            );

        const saveSetupButton =
            document.getElementById(
                "save-setup-button"
            );

        const setupStatus =
            document.getElementById(
                "setup-status"
            );

        let selectedMamePath = "";
        let selectedRomPath = "";

        function updateSaveButton() {{
            saveSetupButton.disabled = !(
                selectedMamePath
                && selectedRomPath
            );
        }}

        chooseMameButton.addEventListener(
            "click",
            async () => {{
                chooseMameButton.disabled = true;

                try {{
                    const selectedPath =
                        await window.pywebview.api
                            .choose_mame_executable();

                    if (selectedPath) {{
                        selectedMamePath =
                            selectedPath;

                        mamePath.textContent =
                            selectedPath;

                        setupStatus.textContent = "";
                        updateSaveButton();
                    }}
                }} catch (error) {{
                    mamePath.textContent = (
                        "Could not open the MAME "
                        + "file picker."
                    );

                    console.error(error);
                }} finally {{
                    chooseMameButton.disabled = false;
                }}
            }}
        );

        chooseRomButton.addEventListener(
            "click",
            async () => {{
                chooseRomButton.disabled = true;

                try {{
                    const selectedPath =
                        await window.pywebview.api
                            .choose_rom_file();

                    if (selectedPath) {{
                        selectedRomPath =
                            selectedPath;

                        romPath.textContent =
                            selectedPath;

                        setupStatus.textContent = "";
                        updateSaveButton();
                    }}
                }} catch (error) {{
                    romPath.textContent = (
                        "Could not open the ROM "
                        + "file picker."
                    );

                    console.error(error);
                }} finally {{
                    chooseRomButton.disabled = false;
                }}
            }}
        );

        saveSetupButton.addEventListener(
            "click",
            async () => {{
                saveSetupButton.disabled = true;
                setupStatus.textContent =
                    "Validating configuration…";

                try {{
                    const result =
                        await window.pywebview.api
                            .save_setup(
                                selectedMamePath,
                                selectedRomPath
                            );

                    if (result.success) {{
                        setupStatus.textContent =
                            "Configuration saved.";

                        window.location.reload();
                        return;
                    }}

                    setupStatus.textContent =
                        result.problems.join(" ");
                }} catch (error) {{
                    setupStatus.textContent = (
                        "Could not save the "
                        + "configuration."
                    );

                    console.error(error);
                }} finally {{
                    updateSaveButton();
                }}
            }}
        );
    </script>
</body>
</html>
"""