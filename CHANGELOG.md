# Changelog

All notable changes to Jungle Gym are documented in this file.

The project uses semantic-style version numbering:

```text
MAJOR.MINOR.PATCH
```

Pre-release builds may additionally use suffixes such as:

```text
-beta.1
```

Jungle Gym is still early software, so features and internal behavior
may change between beta releases.

## [Unreleased]

Public-beta preparation for the next planned build:

```text
v0.1.0-beta.1
```

### Added

- Windows x64 packaging through PyInstaller
- Windows installer configuration through Inno Setup
- Per-game logical session IDs
- Per-game career exclusion markers
- **Excluded from Career** history section
- **Include in Career** support for previously excluded games
- Logical-session detail generation for individual credits
- Backward-compatible handling of legacy whole-launch exclusion markers
- Filtering of zero-duration ghost game boundaries

### Changed

- Jungle Gym now treats **one credit / one game as one session**
- Multiple credits played during one MAME process are analyzed as
  independent career records
- Career statistics, recent-session history, performance graphs, and
  session details now operate on individual games instead of entire MAME
  launches
- Launch controls were simplified to one **Play Now** button
- Every Jungle Gym launch now records telemetry automatically
- The old tracked/untracked player-facing distinction was removed
- The launcher now always activates the Jungle Gym telemetry plugin
- The tracker plugin is loaded from Jungle Gym's bundled plugin path
  instead of being copied into the user's MAME installation
- Gameplay telemetry output paths are passed to the plugin at launch time
- The **Tracked Sessions** dashboard card now shows completed versus
  incomplete game counts instead of a mixed skipped-record count

### Fixed

- Recovered valid individual scores that were previously hidden by
  multi-game launch aggregation
- Prevented a later score reset from causing an earlier completed game to
  appear as a zero-score session
- Prevented one launch-level exclusion from unintentionally removing
  every valid game played later in the same MAME process
- Preserved legitimate incomplete games while filtering zero-activity
  ghost session boundaries
- Confirmed per-game exclude/re-include behavior updates career totals and
  performance graphs in both directions
- Fixed MAME plugin search-path handling for all launcher paths
- Preserved compatibility with MAME 0.225 during tracker/plugin changes

### Repository and release preparation

- Removed runtime telemetry and handoff files from Git history
- Removed a personal email address from historical Git author/committer
  metadata in favor of the GitHub noreply address
- Audited repository history for obvious ROMs, executables, archives,
  credentials, secrets, and other inappropriate release artifacts
- Added release-focused documentation refresh and developer handoff
  material

## [0.1.0] - 2026-08-08

Internal pre-release milestone used during early Jungle Gym packaging and
testing. This version was not the final public-beta baseline.

### Added

- Dedicated Jungle Gym desktop dashboard
- Donkey Kong launch controls
- Local gameplay telemetry capture
- Session history and detailed session views
- Career statistics
- Personal-best tracking
- Performance-history visualization
- Live-session information
- Session exclusion from career statistics
- Customizable dashboard modules
- Persistent dashboard preferences
- Restore-defaults option for dashboard customization
- Empty-career and first-run dashboard states
- Support & Diagnostics page
- Copyable diagnostic reports with home-directory path redaction
- Quick access to the Jungle Gym user-data folder
- Jungle Gym application branding and custom icon
- macOS application bundle and DMG packaging
- Bundled Chart.js for fully local chart rendering
- macOS installation documentation
- Privacy notice
- Legal notice

### Changed

- Retained the existing `DK Tracker` application-data directory for
  compatibility while adopting the Jungle Gym product name
- Session charts load Chart.js locally instead of from an external
  content-delivery network
- Operating-system diagnostics show a user-friendly platform name
  alongside lower-level kernel information

### Fixed

- Prevented duplicate Jungle Gym application windows
- Prevented Donkey Kong attract-mode activity from incorrectly starting
  tracked gameplay sessions
- Improved handling of missing first-run application-data directories

### Platform notes

#### macOS

The original 0.1.0 development build targeted Intel (`x86_64`) Macs and
was unsigned and unnotarized.

#### Windows

Windows packaging was not yet part of the 0.1.0 internal milestone.

### Privacy

Jungle Gym operates locally and does not require an account or cloud
service for normal gameplay tracking.

Gameplay telemetry is stored locally and is not automatically
transmitted to the developer.

See [PRIVACY.md](PRIVACY.md) for details.

### Legal

Jungle Gym is an unofficial fan project and does not include MAME or game
ROMs.

See [LEGAL.md](LEGAL.md) for details.
