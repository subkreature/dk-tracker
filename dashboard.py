#!/usr/bin/env python3

from __future__ import annotations

import threading

import webview

from tracker.config import (
    AppConfig,
    save_config,
    validate_config,
)
from tracker.config import (
    AppConfig,
    save_config,
    validate_config,
)

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
class AppApi:
    """
    Expose native desktop actions to the dashboard.
    """

    def __init__(self) -> None:
        self.window: webview.Window | None = None

    def set_window(
        self,
        window: webview.Window,
    ) -> None:
        """
        Store the native DK Tracker window.
        """

        self.window = window

    def ping(self) -> str:
        """
        Confirm that the JavaScript API bridge is available.
        """

        return "DK Tracker API ready"

    def choose_mame_executable(self) -> str:
        """
        Open a native picker for the MAME executable.

        Return an empty string when the user cancels.
        """

        if self.window is None:
            return ""

        selected_files = (
            self.window.create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=False,
            )
        )

        if not selected_files:
            return ""

        return str(selected_files[0])
    def save_setup(
        self,
        mame_executable: str,
        rom_file: str,
    ) -> dict[str, object]:
        """
        Validate and save the first-run configuration.
        """

        config = AppConfig(
            mame_executable=mame_executable,
            rom_file=rom_file,
        )

        problems = validate_config(config)

        if problems:
            return {
                "success": False,
                "problems": problems,
            }

        save_config(config)

        return {
            "success": True,
            "problems": [],
        }
    def choose_rom_file(self) -> str:
        """
        Open a native picker for dkong.zip.

        Return an empty string when the user cancels.
        """

        if self.window is None:
            return ""

        selected_files = (
            self.window.create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=False,
                file_types=(
                    "ZIP archives (*.zip)",
                    "All files (*.*)",
                ),
            )
        )

        if not selected_files:
            return ""

        return str(selected_files[0])

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
    app_api = AppApi()
    try:
        window = webview.create_window(
            "DK Tracker",
            dashboard_url,
            width=1100,
            height=850,
            min_size=(800, 650),
            js_api=app_api,
        )

        app_api.set_window(window)

        webview.start()

    finally:
        print()
        print("Stopping dashboard...")
        server.shutdown()
        server.server_close()
        print("Dashboard stopped.")


if __name__ == "__main__":
    main()