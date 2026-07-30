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
    </main>
</body>
</html>
"""