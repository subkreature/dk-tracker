# Installing Jungle Gym on macOS

This guide covers installation and first-time setup of Jungle Gym on
macOS.

## Current platform status

An Intel (`x86_64`) macOS build has been developed and tested.

Apple Silicon has not yet been formally tested.

The macOS build should receive a final regression pass after the current
cross-platform tracking model is frozen and before a new public macOS
build is published.

The current macOS build is not code-signed or notarized. macOS may
therefore display a security warning the first time it is opened.

## Before installing

Jungle Gym does not include MAME or any game ROMs.

You must already have:

- A working macOS installation of MAME
- Your own lawful copy of the Donkey Kong ROM set
- A ROM archive named exactly `dkong.zip`

Development testing has included an Intel build of MAME 0.286.

Other MAME versions may work but should be considered unverified until
tested.

## Install Jungle Gym

1. Download the Jungle Gym macOS DMG from the project's official release
   location.
2. Double-click the DMG to mount it.
3. Drag **Jungle Gym.app** onto the **Applications** shortcut.
4. Wait for the copy to finish.
5. Eject the Jungle Gym disk image.
6. Open the Applications folder.
7. Double-click **Jungle Gym**.

Do not run Jungle Gym directly from inside the mounted DMG.

## macOS security warning

Because the current build is not signed or notarized, macOS may prevent
it from opening automatically.

Only continue if you obtained Jungle Gym from a source you trust.

After attempting to open Jungle Gym:

1. Open **System Settings**.
2. Select **Privacy & Security**.
3. Scroll to the **Security** section.
4. Find the message indicating that Jungle Gym was blocked.
5. Click **Open Anyway**.
6. Confirm that you want to open the application.
7. Enter your Mac login password if prompted.

Once approved, Jungle Gym should open normally in the future.

Do not disable Gatekeeper globally.

If macOS says the application is damaged, has been modified, or will
damage your computer, do not override the warning. Delete that copy and
obtain a fresh download from the project's official release location.

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

Jungle Gym does not download, provide, or modify the contents of the ROM
archive.

### Save the configuration

After both paths are selected:

1. Click **Save and Continue**.
2. Confirm that the main Jungle Gym dashboard appears.
3. Open **Support & Diagnostics**.
4. Verify that the configured MAME executable and Donkey Kong ROM are
   available.

## Play Donkey Kong

Jungle Gym now records every game launched through **Play Now**.

To verify the complete setup:

1. Click **Play Now**.
2. Wait for MAME to open.
3. Start a normal credit of Donkey Kong.
4. Confirm that the **Live Session** module appears in Jungle Gym.
5. Play normally.
6. You may play additional credits without closing MAME.
7. Close MAME when finished.
8. Return to Jungle Gym.
9. Confirm that each real credit appears as its own Jungle Gym session.

One credit / game is treated as one logical session.

## Excluding a game from career statistics

Every game is recorded first.

If a test run, accidental credit, or other game should not affect career
statistics:

1. Find the game in **Recent Sessions**.
2. Click **Exclude**.
3. Confirm the exclusion.

The game is removed from career statistics and performance graphs but is
not deleted.

It remains visible under **Excluded from Career**.

To restore it, click **Include**.

## MAME plugin behavior

Jungle Gym uses its bundled `dktracker` plugin for telemetry.

The current launcher adds Jungle Gym's bundled plugin directory to
MAME's plugin search path and activates the plugin for the launch.

Jungle Gym does **not** need to copy the plugin into the configured MAME
installation before each game.

## Local data

Jungle Gym stores configuration, preferences, and gameplay history in:

```text
~/Library/Application Support/DK Tracker
```

The older `DK Tracker` internal folder name is intentionally retained for
compatibility with existing installations.

The folder may contain files and directories such as:

```text
config.json
dashboard-settings.json
data/
```

Gameplay history is stored beneath:

```text
~/Library/Application Support/DK Tracker/data/sessions
```

Use **Support & Diagnostics → Open Data Folder** to open the Jungle Gym
data location in Finder.

## Updating Jungle Gym

Installing a newer Jungle Gym application should not normally erase
personal session data because the data is stored outside the application
bundle.

While Jungle Gym is in beta, create a backup before major updates.

To update:

1. Quit Jungle Gym.
2. Quit MAME.
3. Back up the `DK Tracker` data folder.
4. Open the newer DMG.
5. Drag the new **Jungle Gym.app** into Applications.
6. Approve replacing the existing application.
7. Open Jungle Gym.
8. Confirm that career totals and historical sessions remain present.
9. Verify the displayed version/build information.

## Backing up career data

To create a manual backup:

1. Open **Support & Diagnostics**.
2. Click **Open Data Folder**.
3. Quit Jungle Gym and MAME.
4. Copy the entire `DK Tracker` folder to a safe location.

Restoring the complete folder should restore configuration, preferences,
and tracked gameplay history from that backup.

## Uninstalling Jungle Gym

To remove only the application:

1. Quit Jungle Gym.
2. Open Applications.
3. Move **Jungle Gym.app** to the Trash.

The separately stored career data is not part of the application bundle.

To also remove all Jungle Gym configuration and gameplay history, delete:

```text
~/Library/Application Support/DK Tracker
```

Deleting that folder permanently removes the locally stored history
unless a backup exists.

## Support and diagnostics

The **Support & Diagnostics** page reports information useful for setup
and troubleshooting, including:

- Jungle Gym version and build
- macOS version and CPU architecture
- Python runtime
- Tracker plugin status
- MAME executable status
- ROM status
- Data and session folder status
- Relevant configuration and plugin paths

Use **Copy Diagnostics** when reporting a problem.

The copied report changes the home-folder prefix to `~` where possible.
Review the report before sharing it because remaining path components may
still reveal local folder names.

## Troubleshooting

### Jungle Gym opens to the setup screen again

Open **Support & Diagnostics** and check whether the configured MAME
executable or ROM is missing.

This can happen if MAME or `dkong.zip` was moved after setup.

### MAME opens, but tracking does not begin

Confirm that:

- Donkey Kong was launched through **Play Now**
- The configured ROM is named exactly `dkong.zip`
- The bundled tracker plugin reports as available
- MAME remains open long enough for a real credit to begin
- The game is not still in attract mode

Copy the diagnostics report when requesting help.

### A game is missing from career statistics

Check the **Excluded from Career** section.

If the game is listed there, click **Include** to restore it to career
analytics.

### Finder does not show the latest app icon

macOS may cache an older icon after replacing an application.

The installed application can still be valid even if Finder temporarily
displays a stale icon. Relaunching Finder or copying the application
under a fresh name can force macOS to refresh the icon cache.

### Historical sessions disappeared after updating

Confirm that this folder still exists:

```text
~/Library/Application Support/DK Tracker/data/sessions
```

Do not create a second empty data folder unless troubleshooting
instructions specifically require it.

## Project notice

Jungle Gym is unofficial fan software and is not affiliated with,
authorized by, sponsored by, or endorsed by Nintendo or the MAME
project.

Jungle Gym does not include MAME, Donkey Kong, game ROMs, or other
third-party game assets.

Users are responsible for supplying and using their own lawful copies.
