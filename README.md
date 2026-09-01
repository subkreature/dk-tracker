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

It launches Donkey Kong, activates its bundled telemetry plugin, records
gameplay locally, and turns individual games into a persistent career
dashboard with live telemetry, personal bests, performance history, and
detailed session views.

Jungle Gym is an unofficial fan project, independently developed and largely vibe-coded.

## Current status

Jungle Gym is currently in **public beta**.

The current public beta is:

```text
v0.1.0-beta.1
```

Windows x64 is the primary release target for the first public beta.

An Intel (`x86_64`) macOS build has also been developed and tested, but
macOS will receive a final regression pass after the current core
tracking model is frozen. Apple Silicon has not yet been formally
tested.

Jungle Gym is still early software. Backing up career data before
updating between beta builds is recommended.

## Features

- Launch Donkey Kong directly through Jungle Gym with a single
  **Play Now** button
- Automatic gameplay tracking on every Jungle Gym launch
- **One credit / one game = one Jungle Gym session**
- Live score, board, lives, duration, and gameplay telemetry
- Persistent career statistics
- Personal-best tracking
- Performance-history visualization
- Recent-session summaries
- Detailed individual session pages
- Per-game **Exclude from Career** and **Include in Career** controls
- Retention of excluded game history without deleting raw telemetry
- Customizable dashboard modules
- Persistent dashboard preferences
- Support & Diagnostics page
- One-click access to the local data folder
- Copyable diagnostics with home-directory privacy protection
- Fully local chart rendering through bundled Chart.js

## How tracking works

Jungle Gym records every game launched through **Play Now**.

A single MAME process can contain several credits. Jungle Gym treats each
credit as its own logical session, so playing several games before
closing MAME does not combine those games into one career record.

A game can be excluded from career analytics afterward. Excluding a game:

- removes it from career statistics and performance graphs
- keeps the underlying gameplay data
- keeps it visible in the **Excluded from Career** history section
- allows it to be included again later

Incomplete games can also be retained when real gameplay occurred before
MAME was closed or the run ended unexpectedly.

## Requirements

Jungle Gym does **not** include MAME or any game ROMs.

You must provide:

- A working MAME installation
- Your own lawful copy of the Donkey Kong ROM set
- A ROM archive named exactly `dkong.zip`

Development testing has included:

- MAME 0.225 on Windows
- Intel MAME 0.286 on macOS

Other MAME versions may work, but should be considered unverified until
tested.

## Installation

### Windows

The current public beta ships as a Windows x64 installer.

See:

[Windows Installation Guide](docs/INSTALL-Windows.md)

The current Windows build is unsigned, so Windows may display a
SmartScreen or unknown-publisher warning.

### macOS

The Intel macOS build is installed from a DMG.

See:

[macOS Installation Guide](docs/INSTALL-macOS.md)

The current macOS build is not code-signed or notarized, so macOS may
require an additional approval step before first launch.

## First-time setup

When Jungle Gym starts without a valid configuration:

1. Select the MAME executable.
2. Select your existing `dkong.zip` ROM archive.
3. Save the configuration.
4. Confirm that the main dashboard appears.
5. Open **Support & Diagnostics** and verify the configured files are
   available.

Jungle Gym does not download MAME or game ROMs.

## MAME integration

Jungle Gym uses its bundled `dktracker` MAME plugin for telemetry.

The current launcher activates the bundled plugin through MAME's plugin
search path. Jungle Gym does **not** need to copy its plugin into the
MAME installation before each launch.

Gameplay telemetry paths are supplied to the plugin at launch time and
stored in Jungle Gym's own user-data directory.

## Local data

Jungle Gym stores configuration, dashboard preferences, and gameplay
history locally.

### Windows

```text
%LOCALAPPDATA%\DK Tracker
```

### macOS

```text
~/Library/Application Support/DK Tracker
```

The older internal folder name `DK Tracker` is intentionally retained so
existing development installations do not lose historical sessions or
settings during the Jungle Gym rebrand.

Gameplay history is stored beneath the application's `data/sessions`
folder.

Removing or replacing the Jungle Gym application does not automatically
mean the separately stored career data has been removed. Back up the
entire `DK Tracker` data folder before major upgrades while the project
is in beta.

## Support and diagnostics

Open **Support & Diagnostics** from the dashboard to inspect information
such as:

- Jungle Gym version and build
- Operating system and architecture
- Python runtime
- Tracker plugin status
- MAME executable status
- Donkey Kong ROM status
- Local data and session folders
- Configuration status

The page can also:

- open the Jungle Gym data folder
- copy a plain-text diagnostic report

Copied diagnostics replace the local home-directory prefix with `~`
where possible to reduce accidental disclosure of the account username.
Always review a diagnostic report before posting it publicly.

## Privacy

Jungle Gym is designed to operate locally.

- No Jungle Gym account is required.
- Normal gameplay tracking does not require a cloud service.
- Career and session data are stored on the user's computer.
- The local dashboard server binds to `127.0.0.1`.
- Jungle Gym does not automatically upload gameplay telemetry to the
  developer.
- Diagnostic reports are copied only when the user explicitly requests
  them.

See the [Privacy Notice](PRIVACY.md) for details.

## Documentation

- [Windows Installation Guide](docs/INSTALL-Windows.md)
- [macOS Installation Guide](docs/INSTALL-macOS.md)
- [Development & Release Handoff](DEVELOPMENT.md)
- [Privacy Notice](PRIVACY.md)
- [Legal Notice](LEGAL.md)
- [Changelog](CHANGELOG.md)

## Development and collaboration

The Jungle Gym source code may be publicly viewable, but the project is
**not currently offered under an open-source license**.

Unless permission is granted separately, public source availability does
not grant permission to redistribute Jungle Gym, publish modified
versions, or release derivative versions under another name.

Bug reports, testing feedback, documentation corrections, and feature
ideas are welcome. Code contributions are accepted only by prior
arrangement while the long-term collaboration model is being
determined.

See [LEGAL.md](LEGAL.md) for the current project terms.

## Near-term release priorities

Before the first public beta:

- Complete sustained multi-credit regression testing
- Verify career/session data integrity after real-world play
- Complete the final Windows clean-install regression
- Refresh and validate release documentation
- Produce release checksums
- Publish a GitHub prerelease and enable issue reporting
- Perform a macOS regression pass before publishing a new macOS build

Features that are useful but not required for the first beta remain on
the post-beta roadmap.

## Unofficial project notice

Jungle Gym is unofficial fan software.

It is not affiliated with, authorized by, sponsored by, or endorsed by
Nintendo or the MAME project.

Jungle Gym does not distribute MAME, Donkey Kong, game ROMs, or other
third-party game assets. Users are responsible for supplying and using
their own lawful copies.

Third-party names, marks, and intellectual property belong to their
respective owners.
