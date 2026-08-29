# Jungle Gym Development & Release Handoff

This document is the practical handoff for returning to Jungle Gym after
a development pause and for preparing a public release.

It describes the current architecture, important files, data model,
release workflow, and known remaining work.

## Current release goal

The immediate goal is a stable public beta rather than completion of the
entire feature roadmap.

First public beta:

```text
v0.1.0-beta.1
```

Primary target:

```text
Windows x64
```

macOS should receive a regression pass after the core model is frozen.
Intel macOS has been tested during development; Apple Silicon has not
been formally tested.

## Core product rule

The current non-negotiable session model is:

> **One quarter / credit / game = one Jungle Gym session.**

A single MAME process may remain open across several credits, but career
analytics must treat each real game as an independent record.

Every game launched through Jungle Gym is tracked first. Users can
exclude or re-include individual games afterward.

## High-level architecture

### Entry points

`dashboard.py`

- Starts the local Jungle Gym dashboard application.
- Hosts or opens the local dashboard UI.

`launcher.py`

- Validates the saved MAME and ROM configuration.
- Creates a physical telemetry folder for a MAME launch.
- Launches MAME with the Jungle Gym tracker plugin enabled.
- Passes telemetry file paths to the plugin through environment
  variables.
- All current Jungle Gym launches are tracked.

### Tracker plugin

`plugins/dktracker/init.lua`

- MAME Lua plugin.
- Reads Donkey Kong memory state.
- Emits score samples and gameplay events.
- Writes telemetry to paths supplied by Jungle Gym.

`plugins/dktracker/plugin.json`

- MAME plugin metadata.

The launcher currently supplies:

```text
JUNGLE_GYM_SCORE_PATH
JUNGLE_GYM_EVENTS_PATH
```

The MAME command adds Jungle Gym's bundled `plugins` directory and the
configured MAME plugin directory to `-pluginspath`, then enables:

```text
-plugin dktracker
```

Jungle Gym no longer needs to copy the plugin into the user's MAME
installation.

### Dashboard and HTTP layer

`tracker/web.py`

- Local HTTP server and dashboard HTML/JavaScript.
- Launch controls.
- Live telemetry endpoint.
- Career dashboard.
- Recent sessions.
- Performance history.
- Per-game exclude/include routes.
- Dashboard preferences.
- Session-detail routing.
- Support/diagnostic routes.

The dashboard server binds locally to:

```text
127.0.0.1
```

### Data model and parsing

`tracker/models.py`

- Core dataclasses such as `Session`, `Career`, and event/sample models.
- A logical game session has its own `session_id`.

`tracker/parser.py`

- Reads score/event CSV telemetry.
- Loads physical MAME-launch folders.
- Splits one physical launch into logical per-credit sessions.
- Filters zero-activity ghost boundaries.
- Loads game-based career data.
- Resolves logical session IDs.
- Reads/writes per-game exclusion state.
- Loads excluded games for the History UI.

`tracker/analyzer.py`

- Calculates session and career statistics.

`tracker/session_detail.py`

- Builds detailed session data.
- Includes a logical-session path that operates on an already-split
  `Session`.

`tracker/session_page.py`

- Renders the individual session page.

### Configuration and support

`tracker/config.py`

- Persistent configuration.
- User-data paths.
- Dashboard preferences.

`tracker/setup_page.py`

- First-run configuration UI.

`tracker/support_page.py`

- Support and diagnostic information.

`tracker/live.py`

- Helpers for live-session telemetry.

`tracker/personal_best.py`

- Personal-best calculations/presentation.

### Packaging

`Jungle Gym.spec`

- PyInstaller build specification.

`Jungle Gym.iss`

- Windows Inno Setup installer source.

`assets/JungleGym.ico`

- Windows application icon.

`assets/JungleGym.icns`

- macOS application icon.

`assets/JungleGym.version.txt`

- Windows version-resource metadata.

## Physical launch folders vs logical game sessions

This distinction is essential.

A physical folder under `data/sessions` currently represents one MAME
process / launch container.

Its raw files can contain several games:

```text
<launch-folder>/
    score_log.csv
    events.csv
```

`split_session_into_games()` uses `game_start` event boundaries to derive
logical sessions.

Logical IDs use the launch timestamp plus a game suffix, for example:

```text
2026-08-23_11-22-55_01
2026-08-23_11-22-55_02
2026-08-23_11-22-55_03
```

The logical game shares the physical launch folder but contains sliced
score/event data in memory.

### Ghost-boundary rule

A detected `game_start` becomes a Jungle Gym session only when telemetry
activity occurs after the initial game boundary.

This filters zero-duration boundaries containing only initial state while
preserving:

- completed zero-point games that later contain death/game-over events
- incomplete games with real score/event activity
- games interrupted by closing MAME

### Incomplete games

A game does not require `game_over` to be retained.

If real gameplay occurred and the run ended because MAME was closed or
tracking stopped, the game can remain as an incomplete session.

## Career exclusions

### Current per-game exclusions

Individual exclusions are stored beneath the physical launch folder:

```text
<launch-folder>/
    .excluded-games/
        <logical-session-id>
```

Excluded games:

- remain on disk
- do not affect normal career analytics
- disappear from performance graphs
- remain visible under **Excluded from Career**
- can be re-included by removing the logical exclusion marker through
  the application

### Legacy exclusions

Older development builds may contain:

```text
.exclude-from-career
```

at the physical launch-folder level.

The parser still honors these legacy whole-launch markers for backward
compatibility.

They should not be used for new per-game exclusions.

## User-data paths

### Windows

```text
%LOCALAPPDATA%\DK Tracker
```

### macOS

```text
~/Library/Application Support/DK Tracker
```

The `DK Tracker` internal name is intentionally retained for historical
compatibility.

Do not rename or migrate this directory casually. Existing users may have
career history stored there.

## Repository safety rules

The public source repository must not contain:

- Donkey Kong ROMs
- MAME executables or redistributed MAME binaries
- user gameplay telemetry
- user configuration files
- machine-specific handoff files
- passwords, API keys, tokens, credentials, or secrets
- local packaging environments
- generated build output

`.gitignore` should continue to exclude runtime telemetry, MAME-generated
files, packaging environments, and build output.

Before the public-repository transition, Git history was rewritten to:

- remove historical runtime telemetry paths
- remove runtime score/event handoff files
- replace a personal commit email with the GitHub noreply address

Verified pre-rewrite Git bundle backups were created outside the
repository.

## Normal development checkpoint

For small fixes, use this rhythm:

```text
make change
test
git status
git diff
git add ...
git commit
git push origin main
```

Prefer one tested logical change per commit.

Keep GitHub reasonably current so it remains an off-machine recovery
point.

## Basic validation

At minimum after modifying Python code:

```powershell
python -m py_compile .\path\to\changed_file.py
```

The repository also contains automated tests under:

```text
tests/
```

Run the available test suite before a release candidate.

Manual gameplay testing remains mandatory because the most important
failures involve real MAME process state and multi-credit behavior.

## Required gameplay regression before public beta

Perform a sustained test covering at least:

1. Start Jungle Gym.
2. Click **Play Now**.
3. Play several credits without closing MAME.
4. Include at least one normal completed game.
5. Include at least one very low or zero-score game.
6. Close MAME during an active game to create a legitimate incomplete
   session.
7. Verify that zero-activity ghost boundaries are not counted.
8. Verify every real credit appears as a separate session.
9. Verify career high, average, median, PBs, and graph values.
10. Open Session Details for several games from the same physical launch.
11. Exclude one individual game.
12. Verify it disappears from career analytics and graphs.
13. Verify it appears under **Excluded from Career**.
14. Re-include it.
15. Verify all analytics restore correctly.
16. Restart Jungle Gym and confirm state persists.
17. Confirm historical data remains readable.

Do not publish a release candidate if a later credit can overwrite or
change the interpretation of a previously completed game.

## Known release-critical verification items

These should be resolved or explicitly documented before
`v0.1.0-beta.1` is published.

### Session durability

Raw telemetry is still stored in a physical MAME-launch container and
logical games are derived from boundaries.

The current model has passed targeted tests, but sustained real-world
multi-credit testing remains release-critical.

If a completed game's interpretation can change after later telemetry is
appended, move to stronger per-game finalization/persistence before
release.

### Live elapsed time

Confirm that the **Elapsed Time** value represents what the UI claims.

If it still measures broad MAME launch wall-clock time instead of active
gameplay time, either:

- fix it before release, or
- relabel/hide it so the beta does not present misleading data

### Last Score and exclusions

Decide final public-beta semantics for **Last Score**.

The intended behavior discussed during development is:

- Last Score = literal most recent real game, even if excluded
- career analytics = included games only
- optionally show an asterisk or **Excluded** indicator when the latest
  score is excluded

This is primarily a UI/semantic cleanup rather than a data-integrity
blocker.

### Dependency reproducibility

The repository should include or clearly document the Python/build
dependencies required to recreate development and packaging environments.

If there is no committed requirements/dependency manifest yet, add one
before treating the public repository as fully reproducible.

### Windows installer regression

Before publishing the installer, verify on a clean Windows machine:

- install
- first-run setup
- Play Now
- live telemetry
- multiple credits
- session details
- exclude/re-include
- application restart
- update over an older build if applicable
- uninstall
- expected preservation/removal behavior for `%LOCALAPPDATA%\DK Tracker`

### macOS regression

Before publishing a new macOS build, repeat the core game/session
regression on macOS.

Do not let macOS packaging block the first Windows beta if the Windows
build is otherwise ready; it is acceptable to publish Windows first and
label macOS as pending additional validation.

## Windows build workflow

From the packaging environment, build using the committed PyInstaller
specification:

```powershell
pyinstaller ".\Jungle Gym.spec"
```

Verify the packaged executable under `dist`.

Then compile:

```text
Jungle Gym.iss
```

with Inno Setup to produce the Windows installer.

Before release, confirm the version is consistent anywhere it appears,
including:

- application metadata
- `assets/JungleGym.version.txt`
- installer metadata
- release tag
- release filename
- changelog

Do not rely on old installer artifacts. Rebuild from the final tagged
source.

## Release checksum

Generate and publish a SHA-256 checksum for each downloadable release
artifact.

On Windows PowerShell:

```powershell
Get-FileHash .\path\to\installer.exe -Algorithm SHA256
```

Record the exact hash in the GitHub Release notes or a checksum file.

## GitHub public-beta workflow

Recommended sequence:

1. Confirm the working tree is clean.
2. Confirm `main` is synchronized with `origin/main`.
3. Run automated tests.
4. Complete the manual gameplay regression.
5. Complete the clean-machine Windows regression.
6. Review repository contents and Git history.
7. Review README, installation guides, privacy, and legal docs.
8. Confirm no ROMs, MAME binaries, telemetry, or private configuration
   are tracked.
9. Confirm version metadata is consistent.
10. Build the final installer from the release commit.
11. Compute SHA-256 checksum(s).
12. Tag the release commit:

```text
v0.1.0-beta.1
```

13. Create a GitHub prerelease.
14. Attach the Windows installer and checksum information.
15. Include known limitations in the release notes.
16. Enable or verify GitHub Issues for bug reports.
17. Download the published artifact once and verify it matches the
    expected checksum.

GitHub should remain the canonical source and release-history location.

An itch.io page can be added later as a friendlier discovery/download
front end without replacing GitHub as the source of truth.

## Public-source licensing posture

Jungle Gym is currently intended to be source-visible but not open
source.

The repository should include `LEGAL.md` and should not add an
open-source license unless the project owner deliberately chooses to do
so later.

Do not describe the project as MIT-, GPL-, BSD-, or otherwise
open-source licensed unless that decision has actually been made.

## Post-beta roadmap

Useful items that should not delay the first stable beta unless they
become necessary to solve a release blocker:

- Automatic score-based career exclusion setting
- Excluded indicator/asterisk for Last Score
- True portable Windows mode
- Installer option for preserving/removing historical user data
- Active-game dashboard simplification
- Active-game-only elapsed timer
- Additional custom career metrics
- Object/enemy telemetry research
- Twitch/stream-facing dashboard or overlay
- Apple Silicon validation
- Code signing and notarization
- Additional release/distribution channels such as itch.io

## Recovery after a long pause

If development resumes after months away:

1. Read this file.
2. Read `README.md` and `CHANGELOG.md`.
3. Run:

```powershell
git status -sb
git log --oneline -10
```

4. Confirm the current user-data location.
5. Run the automated tests.
6. Launch the development dashboard.
7. Perform a short multi-credit regression.
8. Review the **Known release-critical verification items** above.
9. Continue from the first unresolved item rather than immediately adding
   a new feature.

The priority order is:

```text
data correctness
→ stability
→ reproducible release
→ documentation
→ new features
```
