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

[Types]
Name: "personalizada"; Description: "Personalizada"; Flags: iscustom

[Components]
; Essenciais: sempre instalados, exibidos para o usuário saber o que entra no PC.
Name: "base"; Description: "Componentes essenciais (sempre instalados)"; Types: personalizada; Flags: fixed
Name: "base\app"; Description: "Serial ClipPRO — o aplicativo"; Types: personalizada; Flags: fixed
Name: "base\ffmpeg"; Description: "FFmpeg — corta e renderiza os vídeos"; Types: personalizada; Flags: fixed; ExtraDiskSpaceRequired: 200000000
Name: "base\ollama"; Description: "Ollama — executa os modelos de IA no seu computador"; Types: personalizada; Flags: fixed; ExtraDiskSpaceRequired: 1500000000
Name: "base\whisper"; Description: "Whisper Small — transcreve as falas das lives"; Types: personalizada; Flags: fixed; ExtraDiskSpaceRequired: 500000000
Name: "base\webview"; Description: "WebView2 — exibe a interface do aplicativo"; Types: personalizada; Flags: fixed
Name: "base\curl"; Description: "curl_cffi — necessário para o fluxo com a Kick"; Types: personalizada; Flags: fixed
; Modelos da curadoria: o usuário escolhe; sem escolha, o mais leve. Dá para trocar depois no app.
Name: "modelos"; Description: "Modelos de IA da curadoria (troque depois em Primeiros Passos)"
Name: "modelos\gemma"; Description: "Gemma 4 12B — Recomendado · precisa de ~10 GB de memória de vídeo"; ExtraDiskSpaceRequired: 8000000000; Flags: dontinheritcheck
Name: "modelos\llama"; Description: "Llama 3.1 8B — Leve · padrão se nenhum for marcado"; ExtraDiskSpaceRequired: 4900000000; Flags: dontinheritcheck
Name: "modelos\qwen35"; Description: "Qwen 3.5 9B — Intermediário"; ExtraDiskSpaceRequired: 6600000000; Flags: dontinheritcheck
Name: "modelos\qwen3"; Description: "Qwen 3 14B — Experimental"; ExtraDiskSpaceRequired: 9300000000; Flags: dontinheritcheck
Name: "gpu"; Description: "Aceleração NVIDIA (CUDA) — transcrição ~4x mais rápida em placas NVIDIA · download de 528 MB"; ExtraDiskSpaceRequired: 772000000

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; Flags: checkedonce

[Files]
Source: "{#PackageDir}\*"; DestDir: "{app}"; Excludes: "Instalar dependencias.bat,install_prereqs.ps1,LEIA-ME.txt"; Components: base\app; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Components: base\app; Flags: ignoreversion
Source: "..\THIRD_PARTY_LICENSES.md"; DestDir: "{app}"; Components: base\app; Flags: ignoreversion
; Cópia para o link da página de componentes, aberta antes da instalação.
Source: "..\THIRD_PARTY_LICENSES.md"; Flags: dontcopy

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
  StatusBase: String;

function PreparationSucceeded: Boolean;
begin
  Result := Ready and not RestartRequired;
end;

function NeedRestart: Boolean;
begin
  Result := RestartRequired;
end;

{ Placa NVIDIA presente: o driver instala o nvidia-smi no System32. }
function TemPlacaNvidia: Boolean;
begin
  Result := FileExists(ExpandConstant('{sys}\nvidia-smi.exe'));
end;

procedure AbrirLicencas(Sender: TObject);
var
  Codigo: Integer;
begin
  ExtractTemporaryFile('THIRD_PARTY_LICENSES.md');
  ShellExec('', ExpandConstant('{sys}\notepad.exe'), AddQuotes(ExpandConstant('{tmp}\THIRD_PARTY_LICENSES.md')), '', SW_SHOWNORMAL, ewNoWait, Codigo);
end;

procedure InitializeWizard;
var
  Rotulo, Link: TNewStaticText;
begin
  if TemPlacaNvidia then
    WizardSelectComponents('gpu');
  { Licença de Terceiros: abaixo da lista de componentes. }
  Rotulo := TNewStaticText.Create(WizardForm);
  Rotulo.Parent := WizardForm.SelectComponentsPage;
  Rotulo.Caption := 'Licença de Terceiros:';
  Rotulo.Left := WizardForm.ComponentsList.Left;
  Rotulo.Top := WizardForm.ComponentsList.Top + WizardForm.ComponentsList.Height + ScaleY(8);
  Link := TNewStaticText.Create(WizardForm);
  Link.Parent := WizardForm.SelectComponentsPage;
  Link.Caption := 'THIRD_PARTY_LICENSES.md';
  Link.Left := Rotulo.Left + Rotulo.Width + ScaleX(6);
  Link.Top := Rotulo.Top;
  Link.Font.Color := clBlue;
  Link.Font.Style := [fsUnderline];
  Link.Cursor := crHand;
  Link.OnClick := @AbrirLicencas;
  WizardForm.ComponentsList.Height := WizardForm.ComponentsList.Height - ScaleY(20);
  Rotulo.Top := WizardForm.ComponentsList.Top + WizardForm.ComponentsList.Height + ScaleY(8);
  Link.Top := Rotulo.Top;
end;

function NenhumModelo: Boolean;
begin
  Result := not (WizardIsComponentSelected('modelos\gemma') or WizardIsComponentSelected('modelos\llama') or
    WizardIsComponentSelected('modelos\qwen35') or WizardIsComponentSelected('modelos\qwen3'));
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = wpSelectComponents) and NenhumModelo then begin
    if WizardSilent then
      WizardSelectComponents('modelos\llama')
    else if MsgBox('Nenhum modelo de IA foi marcado.' + #13#10 + #13#10 +
        'O Llama 3.1 8B, o mais leve (4,9 GB), será instalado como padrão.' + #13#10 +
        'Você pode baixar outros modelos depois, em Primeiros Passos.' + #13#10 + #13#10 +
        'Continuar com o Llama 3.1?', mbConfirmation, MB_YESNO) = IDYES then
      WizardSelectComponents('modelos\llama')
    else
      Result := False;
  end;
end;

function ModelosEscolhidos: String;
begin
  Result := '';
  if WizardIsComponentSelected('modelos\gemma') then Result := Result + 'gemma4:12b,';
  if WizardIsComponentSelected('modelos\llama') then Result := Result + 'llama3.1,';
  if WizardIsComponentSelected('modelos\qwen35') then Result := Result + 'qwen3.5:9b,';
  if WizardIsComponentSelected('modelos\qwen3') then Result := Result + 'qwen3:14b,';
  if Result = '' then Result := 'llama3.1,';
  Delete(Result, Length(Result), 1);
end;

{ Cada linha "@@PROGRESSO|pct|mensagem" do bootstrap move a barra e troca o texto. }
procedure LerProgresso(const S: String; const Error, FirstLine: Boolean);
var
  Resto: String;
  Separador, Percentual: Integer;
begin
  if Copy(S, 1, 12) <> '@@PROGRESSO|' then Exit;
  Resto := Copy(S, 13, Length(S));
  Separador := Pos('|', Resto);
  if Separador = 0 then Exit;
  Percentual := StrToIntDef(Copy(Resto, 1, Separador - 1), -1);
  if (Percentual >= 0) and (Percentual <= 100) then
    WizardForm.ProgressGauge.Position := Percentual;
  WizardForm.StatusLabel.Caption := StatusBase;
  WizardForm.FilenameLabel.Caption := Copy(Resto, Separador + 1, Length(Resto));
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ExitCode: Integer;
  Started: Boolean;
  Retry: Integer;
  Parametros: String;
begin
  if CurStep <> ssPostInstall then Exit;
  Ready := False;
  Parametros := '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\bootstrap.ps1') +
    '" -SkipLaunch -Modelos "' + ModelosEscolhidos + '"';
  if WizardIsComponentSelected('gpu') then
    Parametros := Parametros + ' -Gpu';
  repeat
    StatusBase := 'Preparando componentes e modelos. Os downloads podem levar vários minutos...';
    WizardForm.StatusLabel.Caption := StatusBase;
    WizardForm.ProgressGauge.Min := 0;
    WizardForm.ProgressGauge.Max := 100;
    WizardForm.ProgressGauge.Position := 0;
    { Sem console: a saída do bootstrap alimenta a barra e o log de instalação. }
    Started := ExecAndLogOutput(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'), Parametros,
      ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ExitCode, @LerProgresso);
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
