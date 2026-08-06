<p align="center">
  <img
    src="assets/jungle-gym-icon-source.png"
    alt="Jungle Gym"
    width="360"
  >
</p>

<h1 align="center">Jungle Gym</h1>

<p align="center">
  Donkey Kong performance tracking and career analytics for MAME.
</p>

## About

Jungle Gym is a desktop companion for players of the original arcade
Donkey Kong through MAME.

It launches the game, installs and activates its bundled telemetry
plugin, records tracked sessions, and turns those sessions into a
persistent performance dashboard.

Jungle Gym is free, independently developed, and largely vibe-coded
software.

## Current status

**Current release:** 0.1.0

The current packaged build supports:

- macOS on Intel (`x86_64`)
- MAME-based Donkey Kong play
- Local, single-player career tracking

A Windows version is planned and is considered a high priority.

Apple Silicon support has not yet been tested.

## Features

- Launch Donkey Kong directly through Jungle Gym
- Choose between tracked and untracked games
- Live score, board, lives, duration, and session telemetry
- Persistent career statistics
- Personal-best tracking
- Performance history
- Recent-session summaries
- Detailed individual session pages
- Session exclusion for tests or unwanted runs
- Customizable dashboard modules
- Support and diagnostics page
- One-click access to the local data folder
- Shareable diagnostics with home-directory privacy protection

## Requirements

Jungle Gym does **not** include MAME or any game ROMs.

You must provide:

- A working MAME installation
- Your own lawful copy of the Donkey Kong ROM
- A ROM archive named exactly `dkong.zip`

The current macOS build has been tested with an Intel build of
MAME 0.286. Other MAME versions may work, but have not yet been
fully validated.

## macOS installation

1. Open the Jungle Gym DMG.
2. Drag **Jungle Gym.app** onto the **Applications** shortcut.
3. Open Jungle Gym from the Applications folder.
4. Select your MAME executable.
5. Select your existing `dkong.zip` ROM.
6. Save the setup and continue to the dashboard.

The current macOS release is not code-signed or notarized. macOS may
display an additional security warning before allowing it to open.

A detailed installation and troubleshooting guide will be available
in `docs/INSTALL-macOS.md`.

## Playing with tracking

Choose **Play with Tracking** to begin a recorded game.

Before launching MAME, Jungle Gym:

1. Verifies the configured MAME and ROM paths.
2. Copies the bundled Jungle Gym telemetry plugin into MAME's plugin
   directory.
3. Creates a new local session folder.
4. Starts MAME with tracking enabled.
5. Reads live telemetry while the game is running.
6. Saves the completed session to the local career history.

Choose **Play without Tracking** when you want to play without adding
the game to your Jungle Gym career statistics.

## Local data

Jungle Gym stores configuration, dashboard preferences, and session
history locally.

On macOS, the current data folder is:

```text
~/Library/Application Support/DK Tracker
```

The older internal folder name is intentionally retained so existing
users do not lose their historical sessions or settings during the
Jungle Gym rebrand.

Removing `Jungle Gym.app` does not automatically remove this data.

## Support and diagnostics

Open **Support & Diagnostics** from the main dashboard to view:

- Jungle Gym version and build
- Operating system and architecture
- Python runtime
- Tracker plugin version
- MAME executable status
- Donkey Kong ROM status
- Local data and session folders
- Configuration-file status
- Bundled and installed plugin paths

The page can also:

- Open the Jungle Gym data folder
- Copy a plain-text diagnostic report

Copied diagnostics replace the local home-directory prefix with `~`
to avoid exposing the account username when the report is shared.

## Privacy

Jungle Gym is designed to operate locally.

- No account is required.
- Career and session information is stored on the user's computer.
- The dashboard server binds to `127.0.0.1`.
- Configuration files contain local MAME and ROM paths.
- Diagnostic reports are copied only when the user explicitly presses
  **Copy Diagnostics**.

A fuller privacy statement will be maintained in `PRIVACY.md`.

## Development and collaboration

Jungle Gym is not currently offered under an open-source license.

Bug reports, testing feedback, documentation suggestions, and feature
ideas are welcome. Code contributions are currently accepted only by
prior arrangement while the long-term collaboration and licensing
model is being determined.

A future open-source release remains under consideration.

## Project roadmap

Near-term priorities include:

- Windows packaging and testing
- Windows installation documentation
- macOS release refinement
- Apple Silicon testing
- Release checksums
- GitHub issue and release workflows
- Code signing and notarization research
- Additional diagnostics and support tools

## Unofficial project notice

Jungle Gym is unofficial fan software.

It is not affiliated with, sponsored by, or endorsed by Nintendo or
the MAME project.

Jungle Gym does not distribute MAME, Donkey Kong, game ROMs, or other
third-party game assets. Users are responsible for supplying and using
their own lawful copies.

Donkey Kong, Nintendo, MAME, and other names and marks referenced by
the project belong to their respective owners.

The Jungle Gym name, application artwork, interface, and original
project materials are independently created.

Rights holders may contact the developer regarding concerns about the
project.

## Contact

Created by **Subkreature (SK.)**

[Visit Subkreature online](https://linktr.ee/subkreature)
