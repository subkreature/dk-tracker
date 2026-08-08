# Changelog

All notable changes to Jungle Gym will be documented in this file.

The project follows semantic-style version numbering: `MAJOR.MINOR.PATCH`.

Jungle Gym is still early in development, so features and internal
behavior may change significantly between releases.

## [0.1.0] - 2026-08-08

Initial public-release version of Jungle Gym.

### Added

- Dedicated Jungle Gym desktop dashboard
- Donkey Kong launch controls for tracked and untracked play
- Automatic MAME tracker-plugin synchronization
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
- Privacy policy
- Legal notice

### Changed

- Retained the existing `DK Tracker` application-data directory for
  compatibility while adopting the Jungle Gym product name
- Session charts now load Chart.js locally instead of from an external
  content-delivery network
- Operating-system diagnostics now show a user-friendly platform name
  alongside lower-level kernel information

### Fixed

- Prevented duplicate Jungle Gym application windows
- Prevented Donkey Kong attract-mode gameplay from incorrectly starting
  tracked telemetry sessions
- Improved handling of missing first-run application-data directories
- Added support for excluding individual sessions from career analytics

### Platform support

#### macOS

The 0.1.0 macOS build currently targets Intel (`x86_64`) Macs.

The application is currently unsigned and unnotarized.

Apple Silicon has not yet been formally tested.

#### Windows

Windows packaging is planned but is not included in this release.

### Privacy

Jungle Gym operates locally and does not require an internet connection
for normal use.

Gameplay telemetry refers to locally recorded MAME gameplay data and is
not automatically transmitted to the developer.

See [PRIVACY.md](PRIVACY.md) for details.

### Legal

Jungle Gym is an unofficial fan project and does not include MAME or
game ROMs.

See [LEGAL.md](LEGAL.md) for details.