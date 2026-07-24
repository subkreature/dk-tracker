#!/usr/bin/env python3

from pathlib import Path
import sys

from tracker.analyzer import (
    analyze_career,
    analyze_session,
)
from tracker.parser import (
    load_career,
    load_session,
)
from tracker.report import (
    print_career_report,
    print_session_report,
)


def is_session_folder(
    folder: Path,
) -> bool:
    return (
        (folder / "score_log.csv").exists()
        or (folder / "events.csv").exists()
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage:")
        print(
            "python3 analytics.py "
            "<session_folder_or_sessions_folder>"
        )
        return 1

    requested_path = Path(sys.argv[1])

    try:
        if is_session_folder(requested_path):
            session = load_session(
                requested_path
            )

            summary = analyze_session(
                session
            )

            print_session_report(
                session,
                summary,
            )

        else:
            career = load_career(
                requested_path
            )

            summary = analyze_career(
                career
            )

            print_career_report(
                career,
                summary,
            )

    except (
        FileNotFoundError,
        NotADirectoryError,
        OSError,
        ValueError,
    ) as error:
        print(error)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())