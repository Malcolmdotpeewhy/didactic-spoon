[Setup]
AppName=LeagueLoop
AppVersion=1.0
DefaultDirName={autopf}\LeagueLoop
DefaultGroupName=LeagueLoop
OutputDir=dist
OutputBaseFilename=LeagueLoop_Installer
SetupIconFile=assets\app.ico
UninstallDisplayIcon={app}\LeagueLoop.exe
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

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
