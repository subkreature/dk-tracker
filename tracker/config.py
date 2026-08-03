from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


APP_FOLDER_NAME = "DK Tracker"


def get_user_data_folder() -> Path:
    """
    Return the platform-appropriate folder for DK Tracker data.

    macOS:
        ~/Library/Application Support/DK Tracker

    Windows:
        %LOCALAPPDATA%\\DK Tracker

    Other platforms:
        ~/.local/share/DK Tracker
    """

    if sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / APP_FOLDER_NAME
        )

    if os.name == "nt":
        local_app_data = os.environ.get(
            "LOCALAPPDATA"
        )

        if local_app_data:
            return (
                Path(local_app_data)
                / APP_FOLDER_NAME
            )

        return (
            Path.home()
            / "AppData"
            / "Local"
            / APP_FOLDER_NAME
        )

    return (
        Path.home()
        / ".local"
        / "share"
        / APP_FOLDER_NAME
    )


USER_DATA_FOLDER = get_user_data_folder()
CONFIG_FILE = USER_DATA_FOLDER / "config.json"
DASHBOARD_SETTINGS_FILE = (
    USER_DATA_FOLDER
    / "dashboard-settings.json"
)
DATA_FOLDER = USER_DATA_FOLDER / "data"
SESSIONS_FOLDER = DATA_FOLDER / "sessions"
SESSION_HISTORY_FILE = DATA_FOLDER / "sessions.csv"


@dataclass(frozen=True)
class DashboardSettings:
    """
    Store user-selected dashboard preferences.
    """

    launch_controls_visible: bool = True
    live_session_visible: bool = True
    career_statistics_visible: bool = True
    personal_bests_visible: bool = True
    performance_history_visible: bool = True
    recent_sessions_visible: bool = True


@dataclass(frozen=True)
class AppConfig:
    """
    Store user-selected DK Tracker paths.
    """

    mame_executable: str = ""
    rom_file: str = ""


def load_config() -> AppConfig:
    """
    Load saved configuration.

    Missing or invalid configuration returns empty values.
    """

    if not CONFIG_FILE.exists():
        return AppConfig()

    try:
        raw_data = json.loads(
            CONFIG_FILE.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return AppConfig()

    if not isinstance(raw_data, dict):
        return AppConfig()

    mame_executable = raw_data.get(
        "mame_executable",
        "",
    )

    rom_file = raw_data.get(
        "rom_file",
        "",
    )

    return AppConfig(
        mame_executable=(
            mame_executable
            if isinstance(mame_executable, str)
            else ""
        ),
        rom_file=(
            rom_file
            if isinstance(rom_file, str)
            else ""
        ),
    )


def save_config(
    config: AppConfig,
) -> None:
    """
    Save configuration as formatted JSON.
    """

    USER_DATA_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    CONFIG_FILE.write_text(
        json.dumps(
            asdict(config),
            indent=4,
        )
        + "\n",
        encoding="utf-8",
    )


def load_dashboard_settings() -> DashboardSettings:
    """
    Load saved dashboard preferences.

    Missing or invalid settings return defaults.
    """

    if not DASHBOARD_SETTINGS_FILE.exists():
        return DashboardSettings()

    try:
        raw_data = json.loads(
            DASHBOARD_SETTINGS_FILE.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return DashboardSettings()

    if not isinstance(raw_data, dict):
        return DashboardSettings()

    defaults = DashboardSettings()

    def read_boolean(
        setting_name: str,
    ) -> bool:
        default_value = getattr(
            defaults,
            setting_name,
        )

        saved_value = raw_data.get(
            setting_name,
            default_value,
        )

        return (
            saved_value
            if isinstance(saved_value, bool)
            else default_value
        )

    return DashboardSettings(
        launch_controls_visible=read_boolean(
            "launch_controls_visible"
        ),
        live_session_visible=read_boolean(
            "live_session_visible"
        ),
        career_statistics_visible=read_boolean(
            "career_statistics_visible"
        ),
        personal_bests_visible=read_boolean(
            "personal_bests_visible"
        ),
        performance_history_visible=read_boolean(
            "performance_history_visible"
        ),
        recent_sessions_visible=read_boolean(
            "recent_sessions_visible"
        ),
    )


def save_dashboard_settings(
    settings: DashboardSettings,
) -> None:
    """
    Save dashboard preferences as formatted JSON.
    """

    USER_DATA_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    DASHBOARD_SETTINGS_FILE.write_text(
        json.dumps(
            asdict(settings),
            indent=4,
        )
        + "\n",
        encoding="utf-8",
    )


def validate_config(
    config: AppConfig,
) -> list[str]:
    """
    Return human-readable configuration problems.

    An empty list means the saved configuration passes
    the basic file and filename checks.
    """

    problems: list[str] = []

    if not config.mame_executable:
        problems.append(
            "No MAME executable has been selected."
        )

    else:
        mame_executable = Path(
            config.mame_executable
        )

        if not mame_executable.exists():
            problems.append(
                "The selected MAME executable "
                "does not exist."
            )

        elif not mame_executable.is_file():
            problems.append(
                "The selected MAME path is not a file."
            )

    if not config.rom_file:
        problems.append(
            "No Donkey Kong ROM has been selected."
        )

    else:
        rom_file = Path(
            config.rom_file
        )

        if not rom_file.exists():
            problems.append(
                "The selected Donkey Kong ROM "
                "does not exist."
            )

        elif not rom_file.is_file():
            problems.append(
                "The selected Donkey Kong ROM "
                "path is not a file."
            )

        elif rom_file.name.lower() != "dkong.zip":
            problems.append(
                "The selected ROM must be named "
                "dkong.zip."
            )

    return problems