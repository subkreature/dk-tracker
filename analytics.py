#!/usr/bin/env python3

from pathlib import Path
import sys

from tracker.analyzer import analyze_session
from tracker.parser import load_session
from tracker.report import print_session_report


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage:")
        print(
            "python3 analytics.py "
            "<session_folder>"
        )
        return 1

    session_path = Path(sys.argv[1])

    try:
        session = load_session(
            session_path
        )

        summary = analyze_session(
            session
        )

    except (
        FileNotFoundError,
        NotADirectoryError,
        OSError,
        ValueError,
    ) as error:
        print(error)
        return 1

    print_session_report(
        session,
        summary,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())