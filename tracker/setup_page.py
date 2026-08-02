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

    <title>Jungle Gym Setup</title>

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
            --danger: var(--danger-red);
            --button-hover: #180018;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            min-height: 100vh;
            margin: 0;
            padding: clamp(18px, 4vw, 40px);
            display: grid;
            place-items: center;
            background:
                radial-gradient(
                    circle at top,
                    #120000 0,
                    var(--page-background) 360px
                );
            color: var(--primary-text);
        }}

        main {{
            position: relative;
            width: min(100%, 760px);
            padding:
                clamp(30px, 5vw, 44px)
                clamp(22px, 5vw, 40px);
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
            letter-spacing: 0.08em;
            text-align: center;
            text-shadow:
                3px 3px 0
                var(--barrel-orange),
                0 0 18px
                rgb(244 186 21 / 0.26);
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

        .notice {{
            position: relative;
            padding: 22px 20px 20px;
            overflow: hidden;
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
                rgb(0 0 0 / 0.34);
        }}

        .notice::before {{
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
        }}

        .notice h2 {{
            margin: 0 0 14px;
            color: var(--barrel-gold);
            font-family:
                "Courier New",
                monospace;
            font-size: 1.15rem;
            font-weight: 900;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            text-shadow:
                1px 1px 0
                var(--barrel-orange);
        }}

        .problems {{
            margin-bottom: 0;
            padding-left: 22px;
            color: var(--danger-red);
        }}

        .instructions {{
            margin: 24px 0 0;
            color: var(--ladder-primary);
            line-height: 1.6;
        }}

        .instructions strong {{
            color: var(--score-yellow);
            font-family:
                "Courier New",
                monospace;
        }}

        .setup-button {{
            width: 100%;
            padding: 14px 18px;
            border-radius: 7px;
            font:
                700 1rem
                "Courier New",
                monospace;
            letter-spacing: 0.03em;
            cursor: pointer;
            transition:
                border-color 120ms ease,
                background 120ms ease,
                color 120ms ease,
                opacity 120ms ease,
                transform 120ms ease;
        }}

        .setup-button:hover:not(:disabled) {{
            transform: translateY(-1px);
        }}

        .setup-button:focus-visible {{
            outline:
                2px solid
                var(--ladder-primary);
            outline-offset: 3px;
        }}

        .file-picker-button {{
            margin-top: 24px;
            border:
                1px solid
                var(--score-yellow);
            background: var(--card-background);
            color: var(--barrel-gold);
            box-shadow:
                inset 0 0 0 1px
                rgb(248 249 25 / 0.06);
        }}

        .file-picker-button:hover:not(:disabled) {{
            background: var(--button-hover);
            color: var(--score-yellow);
        }}

        .selected-path {{
            margin: 14px 0 0;
            overflow-wrap: anywhere;
            color: var(--ladder-primary);
            font-family:
                "Courier New",
                monospace;
            font-size: 0.86rem;
            opacity: 0.86;
        }}

        .save-setup-button {{
            margin-top: 28px;
            border:
                1px solid
                var(--score-yellow);
            background: var(--barrel-gold);
            color: #000000;
            font-weight: 900;
            box-shadow:
                inset 0 -3px 0
                var(--barrel-orange),
                0 0 12px
                rgb(248 249 25 / 0.16);
        }}

        .save-setup-button:hover:not(:disabled) {{
            background: var(--score-yellow);
        }}

        .setup-button:disabled {{
            border-color:
                rgb(236 49 147 / 0.36);
            background: #090009;
            color:
                rgb(254 252 255 / 0.38);
            box-shadow: none;
            cursor: not-allowed;
            opacity: 0.72;
        }}

        .setup-status {{
            min-height: 24px;
            margin: 14px 0 0;
            overflow-wrap: anywhere;
            color: var(--ladder-primary);
            font-family:
                "Courier New",
                monospace;
            font-size: 0.86rem;
        }}
    </style>
</head>

<body>
    <main>
        <h1>JUNGLE GYM</h1>

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
            Jungle Gym needs the location of your MAME
            executable and your existing
            <strong>dkong.zip</strong> ROM before it can
            launch Donkey Kong.
        </p>

        <button
            id="choose-mame-button"
            class="setup-button file-picker-button"
            type="button"
        >
            Choose MAME Executable…
        </button>

        <p
            id="mame-path"
            class="selected-path"
        >
            No MAME executable selected.
        </p>

        <button
            id="choose-rom-button"
            class="setup-button file-picker-button"
            type="button"
        >
            Choose dkong.zip…
        </button>

        <p
            id="rom-path"
            class="selected-path"
        >
            No Donkey Kong ROM selected.
        </p>

        <button
            id="save-setup-button"
            class="setup-button save-setup-button"
            type="button"
            disabled
        >
            Save and Continue
        </button>

        <p
            id="setup-status"
            class="setup-status"
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