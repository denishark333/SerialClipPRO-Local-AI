#ifndef PackageDir
  #define PackageDir "..\dist\Serial ClipPRO"
#endif
#ifndef AppVersion
  #define AppVersion "2.0.0"
#endif
#ifndef InstallerOutput
  #define InstallerOutput "..\dist\installer"
#endif
#ifndef InstallerAppId
  #define InstallerAppId "{{2919A7E7-B72A-46E0-8B52-EBDA4156C27D}"
#endif
#ifndef InstallerGroup
  #define InstallerGroup "Serial ClipPRO"
#endif

[Setup]
AppId={#InstallerAppId}
AppName=Serial ClipPRO
AppVersion={#AppVersion}
AppPublisher=Serial Healer
AppPublisherURL=https://github.com/denishark333/SerialClipPRO-Local-AI
DefaultDirName={localappdata}\Programs\Serial ClipPRO
DefaultGroupName={#InstallerGroup}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0
OutputDir={#InstallerOutput}
OutputBaseFilename=Serial-ClipPRO-{#AppVersion}-Setup-x64
SetupIconFile=..\assets\serial-clippro.ico
UninstallDisplayIcon={app}\Serial ClipPRO.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=no
RestartApplications=no
AppMutex=SerialClipPRO.Desktop
UninstallDisplayName=Serial ClipPRO

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; Flags: checkedonce

[Files]
Source: "{#PackageDir}\*"; DestDir: "{app}"; Excludes: "Instalar dependencias.bat,install_prereqs.ps1,LEIA-ME.txt"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Serial ClipPRO"; Filename: "{app}\Serial ClipPRO.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Serial ClipPRO"; Filename: "{app}\Serial ClipPRO.exe"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{group}\Preparar ou reparar Serial ClipPRO"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\bootstrap.ps1"""; WorkingDir: "{app}"; IconFilename: "{app}\Serial ClipPRO.exe"

[Run]
Filename: "{app}\Serial ClipPRO.exe"; Description: "Abrir Serial ClipPRO"; Flags: nowait postinstall skipifsilent; Check: PreparationSucceeded

[Code]
var
  Ready: Boolean;
  RestartRequired: Boolean;

function PreparationSucceeded: Boolean;
begin
  Result := Ready and not RestartRequired;
end;

function NeedRestart: Boolean;
begin
  Result := RestartRequired;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ExitCode: Integer;
  Started: Boolean;
  Retry: Integer;
begin
  if CurStep <> ssPostInstall then Exit;
  Ready := False;
  repeat
    WizardForm.StatusLabel.Caption := 'Preparando componentes e modelos. O download pode levar vários minutos...';
    Started := Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
      '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\bootstrap.ps1') + '" -SkipLaunch',
      ExpandConstant('{app}'), SW_SHOW, ewWaitUntilTerminated, ExitCode);
    if Started and (ExitCode = 0) then begin
      Ready := True;
      Exit;
    end;
    if Started and (ExitCode = 3010) then begin
      RestartRequired := True;
      Exit;
    end;
    if WizardSilent then Exit;
    Retry := MsgBox('A preparação não foi concluída. Consulte o diagnóstico para identificar a etapa que falhou.' + #13#10 +
      'Diagnóstico: %LOCALAPPDATA%\Serial ClipPRO\instalacao.log' + #13#10 +
      'Você também pode retomar pelo atalho "Preparar ou reparar Serial ClipPRO" no menu Iniciar.', mbError, MB_RETRYCANCEL);
  until Retry <> IDRETRY;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID = wpFinished) and not Ready then
    WizardForm.FinishedLabel.Caption := 'Os arquivos foram instalados, mas a preparação ainda está pendente.' + #13#10 +
      'Se houver reinicialização pendente, reinicie o Windows. Depois use "Preparar ou reparar Serial ClipPRO" no menu Iniciar para concluir.';
end;

function GetCustomSetupExitCode: Integer;
begin
  if RestartRequired then Result := 3010
  else if not Ready then Result := 1
  else Result := 0;
end;
