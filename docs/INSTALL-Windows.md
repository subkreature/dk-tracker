# Installing Jungle Gym on Windows

This guide covers installation and first-time setup of Jungle Gym on
Windows.

## Current platform status

Windows x64 is the primary target for the first Jungle Gym public beta.

The release candidate is packaged as a Windows application and installer.

Final clean-machine regression testing should be completed before each
public installer is published.

The current Windows build is not code-signed. Windows may therefore show
a Microsoft Defender SmartScreen or unknown-publisher warning.

Only continue if the installer came from the project's official release
location.

## Before installing

Jungle Gym does not include MAME or any game ROMs.

You must already have:

- A working Windows installation of MAME
- Your own lawful copy of the Donkey Kong ROM set
- A ROM archive named exactly `dkong.zip`

Development testing has included MAME 0.225.

Other MAME versions may work but should be considered unverified until
tested.

## Install Jungle Gym

1. Download the current Jungle Gym Windows installer from the project's
   official GitHub Release.
2. Close MAME and any older Jungle Gym process.
3. Run the installer.
4. If Windows displays a SmartScreen or unknown-publisher warning, verify
   that the file came from the official release before choosing to
   continue.
5. Complete the installer.
6. Launch **Jungle Gym**.

Do not download MAME or Donkey Kong ROMs from links claiming to be part
of Jungle Gym. They are not included with the project.

## First-time setup

When Jungle Gym opens without a valid configuration, it displays its
first-run setup screen.

### Choose the MAME executable

1. Click **Choose MAME Executable…**
2. Navigate to the MAME installation.
3. Select the MAME executable itself, normally:

```text
mame.exe
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

Jungle Gym does not download, provide, or modify the ROM archive.

### Save the configuration

After both paths are selected:

1. Click **Save and Continue**.
2. Confirm that the main Jungle Gym dashboard appears.
3. Open **Support & Diagnostics**.
4. Verify that the configured MAME executable and Donkey Kong ROM are
   available.

## Play Donkey Kong

Jungle Gym records every game launched through **Play Now**.

To verify the complete setup:

1. Click **Play Now**.
2. Wait for MAME to open.
3. Start a normal credit of Donkey Kong.
4. Confirm that the **Live Session** module appears.
5. Play normally.
6. You may play multiple credits before closing MAME.
7. Close MAME when finished.
8. Return to Jungle Gym.
9. Confirm that each real credit appears as its own Jungle Gym session.

One credit / game is treated as one logical session.

## Excluding a game from career statistics

Every game is recorded first.

If a game should not affect career analytics:

1. Find it under **Recent Sessions**.
2. Click **Exclude**.
3. Confirm the exclusion.

The game remains stored but is removed from career statistics and
performance graphs.

It appears under **Excluded from Career** with an **Include** button.

Click **Include** to restore it.

## MAME plugin behavior

Jungle Gym uses its bundled `dktracker` plugin.

The launcher adds both Jungle Gym's bundled plugin location and MAME's
plugin directory to MAME's plugin search path, then activates the
Jungle Gym tracker plugin.

The current architecture does not require Jungle Gym to copy its plugin
into the user's MAME installation before each launch.

## Local data

Jungle Gym stores user configuration, dashboard preferences, and gameplay
history beneath:

```text
%LOCALAPPDATA%\DK Tracker
```

Gameplay history is stored beneath:

```text
%LOCALAPPDATA%\DK Tracker\data\sessions
```

The older `DK Tracker` folder name is retained for compatibility with
existing development installations.

Use **Support & Diagnostics → Open Data Folder** to open the data
location.

## Updating Jungle Gym

User data is stored separately from the installed application files.

While Jungle Gym is in beta, back up the `DK Tracker` data folder before
major updates.

A safe update procedure is:

1. Quit Jungle Gym.
2. Quit MAME.
3. Back up `%LOCALAPPDATA%\DK Tracker`.
4. Install the newer Jungle Gym build.
5. Launch Jungle Gym.
6. Confirm that the existing career history is present.
7. Open **Support & Diagnostics** and verify the current build and paths.

## Backing up career data

To create a manual backup:

1. Open **Support & Diagnostics**.
2. Click **Open Data Folder**.
3. Quit Jungle Gym and MAME.
4. Copy the entire `DK Tracker` folder to a safe location.

## Uninstalling Jungle Gym

The application and its user-data folder are separate.

Before deleting any local Jungle Gym data, back up the `DK Tracker`
folder if the career history should be preserved.

Current public-release testing should verify installer/uninstaller data
preservation behavior before each build is published.

To manually remove all Jungle Gym user data after uninstalling the
application, delete:

```text
%LOCALAPPDATA%\DK Tracker
```

This permanently removes local configuration, preferences, and gameplay
history unless a backup exists.

## Support and diagnostics

The **Support & Diagnostics** page provides setup and troubleshooting
information such as:

- Jungle Gym version and build
- Windows version and architecture
- Python runtime
- Tracker plugin status
- MAME executable status
- ROM status
- Data and session folder status
- Relevant configuration and plugin paths

Use **Copy Diagnostics** when reporting a problem and review the copied
text before posting it publicly.

## Troubleshooting

### Windows blocks the installer

The current beta build may be unsigned.

Verify that the installer was downloaded from the project's official
GitHub Release before choosing to continue.

Do not disable Windows security features globally.

### Jungle Gym opens to setup again

Open **Support & Diagnostics** and verify that the configured MAME
executable and `dkong.zip` still exist at the saved locations.

### MAME opens, but tracking does not begin

Confirm that:

- Donkey Kong was launched through **Play Now**
- The configured ROM is named exactly `dkong.zip`
- The bundled tracker plugin reports as available
- MAME remains open long enough for a real credit to begin
- The game is not still in attract mode

### A game is missing from career statistics

Check the **Excluded from Career** section.

If the game is listed there, click **Include**.

## Project notice

Jungle Gym is unofficial fan software and is not affiliated with,
authorized by, sponsored by, or endorsed by Nintendo or the MAME
project.

Jungle Gym does not include MAME, Donkey Kong, game ROMs, or other
third-party game assets.

Users are responsible for supplying and using their own lawful copies.
