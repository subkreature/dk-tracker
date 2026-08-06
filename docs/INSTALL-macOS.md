# Installing Jungle Gym on macOS

This guide covers installation and first-time setup of Jungle Gym on
macOS.

## Current platform support

The current Jungle Gym release supports:

- Intel Macs (`x86_64`)
- MAME-based Donkey Kong play
- Local, single-player career tracking

Apple Silicon has not yet been tested.

Jungle Gym 0.1.0 is not currently code-signed or notarized. macOS may
therefore display a security warning the first time it is opened.

## Before installing

Jungle Gym does not include MAME or any game ROMs.

You must already have:

- A working macOS installation of MAME
- Your own lawful copy of the Donkey Kong ROM
- A ROM archive named exactly `dkong.zip`

The initial macOS release has been tested with an Intel build of
MAME 0.286.

Other MAME versions may work, but have not yet been fully validated.

## Install Jungle Gym

1. Download the Jungle Gym macOS DMG.
2. Double-click the DMG to mount it.
3. Drag **Jungle Gym.app** onto the **Applications** shortcut.
4. Wait for the copy to finish.
5. Eject the Jungle Gym disk image.
6. Open the Applications folder.
7. Double-click **Jungle Gym**.

Do not run Jungle Gym directly from inside the mounted DMG.

## macOS security warning

Because the current release is not signed or notarized, macOS may
prevent it from opening automatically.

Only continue if you obtained Jungle Gym from a source you trust.

After attempting to open Jungle Gym:

1. Open **System Settings**.
2. Select **Privacy & Security**.
3. Scroll down to the **Security** section.
4. Find the message indicating that Jungle Gym was blocked.
5. Click **Open Anyway**.
6. Confirm that you want to open the application.
7. Enter your Mac login password if prompted.

Once approved, Jungle Gym should open normally in the future.

Do not disable Gatekeeper globally.

If macOS says the application is damaged, has been modified, or will
damage your computer, do not override the warning. Delete that copy
and obtain a fresh download from the project’s official release
location.

## First-time setup

When Jungle Gym opens without a valid configuration, it displays its
first-run setup screen.

### Choose the MAME executable

1. Click **Choose MAME Executable…**
2. Navigate to your MAME installation.
3. Select the MAME executable itself.

For a standalone MAME download, this is commonly the file named:

```text
mame
```

Do not select the containing folder.

### Choose the Donkey Kong ROM

1. Click **Choose dkong.zip…**
2. Navigate to the ROM folder used by MAME.
3. Select:

```text
dkong.zip
```

The file must be named exactly `dkong.zip`.

Jungle Gym does not download, provide, or modify the contents of the
ROM archive.

### Save the configuration

After both paths are selected:

1. Click **Save and Continue**.
2. Confirm that the main Jungle Gym dashboard appears.
3. Open **Support & Diagnostics**.
4. Verify that the MAME executable and Donkey Kong ROM both show
   **Available**.

## Play a tracked game

To verify the complete setup:

1. Click **Play with Tracking**.
2. Wait for MAME to open.
3. Begin a normal game of Donkey Kong.
4. Confirm that the **Live Session** module appears in Jungle Gym.
5. End the game normally.
6. Close MAME.
7. Return to Jungle Gym.
8. Confirm that the game appears under **Recent Sessions**.

Jungle Gym automatically copies its bundled telemetry plugin into the
configured MAME plugin folder before launching the game.

A tracked session should not require manually installing the plugin.

## Play without tracking

Use **Play without Tracking** when you want Jungle Gym to launch MAME
without adding the game to career statistics.

An untracked game should not appear in Recent Sessions or affect
personal bests and career totals.

## Local data

Jungle Gym stores configuration, preferences, and tracked sessions in:

```text
~/Library/Application Support/DK Tracker
```

The older `DK Tracker` internal folder name is intentionally retained
for compatibility with existing installations.

The folder may contain:

```text
config.json
dashboard-settings.json
data/
```

Tracked session folders are stored beneath:

```text
~/Library/Application Support/DK Tracker/data/sessions
```

Use **Support & Diagnostics → Open Data Folder** to open this location
in Finder.

## Updating Jungle Gym

Installing a newer Jungle Gym application should not erase personal
session data because the data is stored outside the application
bundle.

To update:

1. Quit Jungle Gym.
2. Open the newer DMG.
3. Drag the new **Jungle Gym.app** into Applications.
4. Approve replacing the existing application.
5. Open Jungle Gym.
6. Confirm that career totals and historical sessions remain present.
7. Verify the version under **Jungle Gym → About Jungle Gym**.

Backing up the Jungle Gym data folder before an update is recommended
while the application is in early development.

## Backing up career data

To create a manual backup:

1. Open **Support & Diagnostics**.
2. Click **Open Data Folder**.
3. Quit Jungle Gym and MAME.
4. Copy the entire `DK Tracker` folder to a safe location.

Restoring that complete folder should restore configuration,
preferences, and tracked sessions from the backup.

## Uninstalling Jungle Gym

To remove only the application:

1. Quit Jungle Gym.
2. Open Applications.
3. Move **Jungle Gym.app** to the Trash.

This does not remove career data.

To also remove all configuration and tracked sessions, delete:

```text
~/Library/Application Support/DK Tracker
```

Deleting that folder permanently removes Jungle Gym’s locally stored
history unless a backup exists.

## Support and diagnostics

The Support & Diagnostics page reports:

- Jungle Gym version and build
- macOS version and CPU architecture
- Python runtime
- Tracker plugin version
- MAME executable status
- ROM status
- Data and session folder status
- Bundled and installed plugin locations

Use **Copy Diagnostics** when reporting a problem.

The copied report changes the home-folder prefix to `~` so the local
account username is not exposed. Review the report before sharing it
because it still contains the remaining MAME, ROM, and data paths.

## Troubleshooting

### Jungle Gym opens to the setup screen again

Open **Support & Diagnostics** and check whether the configured MAME
executable or ROM is now missing.

This can happen if MAME or `dkong.zip` was moved after setup.

### MAME opens, but tracking does not begin

Confirm that:

- The game was launched with **Play with Tracking**
- The configured ROM is named `dkong.zip`
- The bundled and installed plugin paths show **Available**
- MAME remains open long enough for a game to begin
- The game is not still running in attract mode

Copy the diagnostics report when requesting help.

### Finder does not show the latest app icon

macOS may cache an older icon after replacing an application.

The installed application can still be valid even if Finder
temporarily displays a stale icon. Relaunching Finder or copying the
application under a fresh name can force macOS to refresh the icon
cache.

### Historical sessions disappeared after updating

Confirm that this folder still exists:

```text
~/Library/Application Support/DK Tracker/data/sessions
```

Do not create a second empty data folder unless troubleshooting
instructions specifically require it.

## Project notice

Jungle Gym is unofficial fan software and is not affiliated with,
sponsored by, or endorsed by Nintendo or the MAME project.

Jungle Gym does not include MAME, Donkey Kong, game ROMs, or other
third-party game assets.

Users are responsible for supplying and using their own lawful copies.