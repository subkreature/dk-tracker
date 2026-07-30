#!/usr/bin/env python3

from __future__ import annotations

import threading

import webview

from tracker.web import (
    HOST,
    PORT,
    create_dashboard_server,
)


def run_server(
    server,
) -> None:
    """
    Run the local dashboard server in the background.
    """

    server.serve_forever()


def main() -> None:
    """
    Start DK Tracker in a dedicated desktop window.
    """

    try:
        server = create_dashboard_server()

    except OSError as error:
        print(
            "Could not start DK Tracker "
            f"dashboard on port {PORT}."
        )
        print(error)
        return

    server_thread = threading.Thread(
        target=run_server,
        args=(server,),
        daemon=True,
        name="dk-dashboard-server",
    )

    server_thread.start()

    dashboard_url = (
        f"http://{HOST}:{PORT}"
    )

    print("===================================")
    print(" DK Tracker")
    print("===================================")
    print()
    print(
        f"Running at: {dashboard_url}"
    )
    print(
        "Opening dedicated application window."
    )
    print()

    try:
        webview.create_window(
            "DK Tracker",
            dashboard_url,
            width=1100,
            height=850,
            min_size=(800, 650),
        )

        webview.start()

    finally:
        print()
        print("Stopping dashboard...")
        server.shutdown()
        server.server_close()
        print("Dashboard stopped.")


if __name__ == "__main__":
    main()