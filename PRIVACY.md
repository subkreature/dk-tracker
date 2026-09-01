# Jungle Gym Privacy Notice

Jungle Gym is designed to operate locally on the user's computer.

It does not require a Jungle Gym account, cloud service, or internet
connection for normal gameplay tracking.

## Data Jungle Gym stores

Jungle Gym stores information needed to configure the application and
maintain the user's Donkey Kong career history.

This may include:

- The configured path to the user's MAME executable
- The configured path to the user's `dkong.zip` ROM
- Dashboard display preferences
- Gameplay telemetry
- Scores and score samples
- Board progression
- Lives and gameplay events
- Timing information
- Completed and incomplete game-session records
- Per-game career exclusion state
- Career and session history derived from tracked games

## Where data is stored

### Windows

Jungle Gym currently stores user data beneath:

```text
%LOCALAPPDATA%\DK Tracker
```

### macOS

Jungle Gym currently stores user data beneath:

```text
~/Library/Application Support/DK Tracker
```

The `DK Tracker` folder name is retained for compatibility with earlier
development versions of Jungle Gym.

Gameplay history is stored beneath the application's local
`data/sessions` directory.

## Gameplay sessions and exclusions

Jungle Gym records gameplay locally when Donkey Kong is launched through
the application.

One credit / game is treated as one logical Jungle Gym session.

When a user excludes a game from career statistics, Jungle Gym keeps the
underlying gameplay data and records an exclusion marker. The game can be
included in career statistics again later.

Excluding a game does not upload or transmit that game to the developer.

## Network behavior

Jungle Gym's dashboard is served locally and binds to:

```text
127.0.0.1
```

Jungle Gym does not currently require a remote account or cloud backend
for normal use.

Jungle Gym does not automatically send gameplay telemetry, career
history, analytics, or crash reports to the developer.

Downloading Jungle Gym from a third-party distribution service such as
GitHub, visiting external links, or using MAME itself may involve
separate network services governed by their own privacy practices.

## Diagnostics

The **Support & Diagnostics** page can generate a plain-text diagnostic
report for troubleshooting.

Diagnostic information is copied only when the user explicitly requests
it.

Where possible, copied diagnostics replace the user's home-directory
prefix with:

```text
~
```

This reduces accidental disclosure of the local account username.

A diagnostic report may still contain remaining MAME, ROM, application,
or data-folder path information. Users should review diagnostic text
before posting or sending it to another person.

Jungle Gym does not automatically transmit copied diagnostics.

## Backups and deletion

Jungle Gym does not currently provide cloud backup.

Users are responsible for backing up local career data if they want an
additional copy.

To back up Jungle Gym completely, quit Jungle Gym and MAME and copy the
entire `DK Tracker` user-data folder.

Deleting the Jungle Gym application does not necessarily delete the
separately stored user-data folder.

Deleting the `DK Tracker` user-data folder removes local configuration,
preferences, and gameplay history unless another backup exists.

## No developer account database

Jungle Gym does not currently maintain a developer-operated account
database containing player profiles or career histories.

If future versions add optional online features, this notice should be
updated before those features are released.
