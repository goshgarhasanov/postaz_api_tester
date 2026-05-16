; Postaz — Inno Setup 6 installer script
;
; Builds Postaz-Setup-{version}.exe — a Next / Next / Finish installer that
; drops the PyInstaller bundle into the user's machine, creates Start Menu
; and (optionally) Desktop shortcuts, and registers an Uninstaller in
; "Apps & features".
;
; Build:
;     "C:\Users\<you>\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer\postaz.iss
;
; or via the build runner:  build\build_installer.ps1

#define MyAppName        "Postaz"
#define MyAppVersion     "2.0.0"
#define MyAppPublisher   "goshgarhasanov"
#define MyAppURL         "https://github.com/goshgarhasanov/postaz_api_tester"
#define MyAppExeName     "Postaz.exe"
#define MyAppID          "{{6F1A8E4A-2C7B-4A4F-9F32-9D9C8B6E0001}}"

[Setup]
AppId={#MyAppID}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; Install per-user under Local AppData by default. This avoids needing
; admin rights and makes the installer feel friendly.
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
DisableDirPage=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

OutputDir=..\installer\dist
OutputBaseFilename=Postaz-Setup-{#MyAppVersion}
SetupIconFile=..\build\postaz.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
WizardResizable=no
ShowLanguageDialog=auto
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} — modern API tester
VersionInfoProductName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; Copy the entire PyInstaller bundle. * recurses; createallsubdirs preserves the tree.
Source: "..\build\dist\Postaz\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}";           Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}";   Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Launch Postaz right after install if the user keeps the checkbox ticked.
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
