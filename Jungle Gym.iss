#define MyAppName "Jungle Gym"
#define MyAppVersion "0.1.0-beta.1"
#define MyAppPublisher "Subkreature (SK.)"
#define MyAppExeName "Jungle Gym.exe"

[Setup]
AppId={{A1D63CB5-50B4-4B91-A2DF-E7565435AE42}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\Jungle Gym
DefaultGroupName=Jungle Gym
DisableProgramGroupPage=yes

SetupArchitecture=x64

OutputDir=installer-output
OutputBaseFilename=Jungle-Gym-0.1.0-beta.1-Setup

SetupIconFile=assets\JungleGym.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\Jungle Gym\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Jungle Gym"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Jungle Gym"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Jungle Gym"; Flags: nowait postinstall skipifsilent
