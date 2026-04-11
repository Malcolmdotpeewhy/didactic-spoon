; LeagueLoop Installer — Inno Setup Script
; Reads version from src/core/version.py at compile time

#define VersionFile ReadIni(SourcePath + "\src\core\version.py", "", "", "")

[Setup]
AppName=LeagueLoop
AppVersion=1-04-264-0219
VersionInfoVersion=1.4.264.219
AppPublisher=Malcolm
AppPublisherURL=https://github.com/Intrusive-Thots/LeagueLoop-Installer
AppSupportURL=https://github.com/Intrusive-Thots/LeagueLoop-Lock/issues
DefaultDirName={autopf}\LeagueLoop
DefaultGroupName=LeagueLoop
OutputDir=dist
OutputBaseFilename=LeagueLoop_Installer
SetupIconFile=assets\app.ico
UninstallDisplayIcon={app}\LeagueLoop.exe
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\LeagueLoop\LeagueLoop.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\LeagueLoop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\LeagueLoop"; Filename: "{app}\LeagueLoop.exe"
Name: "{autodesktop}\LeagueLoop"; Filename: "{app}\LeagueLoop.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\LeagueLoop.exe"; Description: "{cm:LaunchProgram,LeagueLoop}"; Flags: nowait postinstall skipifsilent
