#ifndef PackageDir
  #define PackageDir "..\dist\Serial ClipPRO"
#endif
#ifndef AppVersion
  #define AppVersion "3.1.0"
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
; A coluna de tamanhos é preenchida pelo código com valores curtos (o Inno mostra casas demais).
ShowComponentSizes=no
DisableProgramGroupPage=yes
CloseApplications=no
RestartApplications=no
AppMutex=SerialClipPRO.Desktop
UninstallDisplayName=Serial ClipPRO
; Pergunta o idioma ao abrir (sugere o do Windows); numa atualização, reaproveita o anterior.
ShowLanguageDialog=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
brazilianportuguese.TipoPersonalizada=Personalizada
english.TipoPersonalizada=Custom
brazilianportuguese.CompBase=Componentes essenciais (sempre instalados)
english.CompBase=Essential components (always installed)
brazilianportuguese.CompApp=Serial ClipPRO — o aplicativo
english.CompApp=Serial ClipPRO — the app
brazilianportuguese.CompFfmpeg=FFmpeg — corta e renderiza os vídeos
english.CompFfmpeg=FFmpeg — cuts and renders the videos
brazilianportuguese.CompOllama=Ollama — executa os modelos de IA no seu computador
english.CompOllama=Ollama — runs the AI models on your computer
brazilianportuguese.CompWhisper=Whisper Small — transcreve as falas das lives
english.CompWhisper=Whisper Small — transcribes the speech in your streams
brazilianportuguese.CompWebview=WebView2 — exibe a interface do aplicativo
english.CompWebview=WebView2 — displays the app interface
brazilianportuguese.CompCurl=curl_cffi — necessário para o fluxo com a Kick
english.CompCurl=curl_cffi — needed for Kick
brazilianportuguese.CompModelos=Modelos de IA da curadoria (troque depois em Primeiros Passos)
english.CompModelos=AI models for curation (switch later in Getting Started)
brazilianportuguese.CompGemma=Gemma 4 12B — Recomendado · requer ~10 GB de memória de vídeo
english.CompGemma=Gemma 4 12B — Recommended · needs ~10 GB of video memory
brazilianportuguese.CompLlama=Llama 3.1 8B — Leve · padrão se nenhum for marcado
english.CompLlama=Llama 3.1 8B — Lightweight · default if none is selected
brazilianportuguese.CompQwen35=Qwen 3.5 9B — Intermediário
english.CompQwen35=Qwen 3.5 9B — Intermediate
brazilianportuguese.CompQwen3=Qwen 3 14B — Experimental
english.CompQwen3=Qwen 3 14B — Experimental
brazilianportuguese.CompGpu=Aceleração NVIDIA (CUDA) — transcrição ~4x mais rápida
english.CompGpu=NVIDIA acceleration (CUDA) — ~4x faster transcription
brazilianportuguese.TarefaAtalho=Criar atalho na área de trabalho
english.TarefaAtalho=Create a desktop shortcut
brazilianportuguese.AbrirApp=Abrir Serial ClipPRO
english.AbrirApp=Open Serial ClipPRO
brazilianportuguese.AtalhoReparar=Preparar ou reparar Serial ClipPRO
english.AtalhoReparar=Prepare or repair Serial ClipPRO
brazilianportuguese.Licencas=Licenças:
english.Licencas=Licenses:
brazilianportuguese.NenhumModelo=Nenhum modelo de IA foi marcado.%n%nSerá instalado o Llama 3.1 8B,%no mais leve (4,9 GB).%n%nOutros modelos podem ser baixados%ndepois, em Primeiros Passos.%n%nContinuar com o Llama 3.1?
english.NenhumModelo=No AI model was selected.%n%nLlama 3.1 8B, the lightest%n(4.9 GB), will be installed.%n%nOther models can be downloaded%nlater in Getting Started.%n%nContinue with Llama 3.1?
brazilianportuguese.StatusPreparando=Preparando componentes e modelos. Os downloads podem levar vários minutos...
english.StatusPreparando=Preparing components and models. Downloads may take several minutes...
brazilianportuguese.PreparacaoFalhou=A preparação não foi concluída. Consulte o diagnóstico para identificar a etapa que falhou.%nDiagnóstico: %1%nVocê também pode retomar pelo atalho "Preparar ou reparar Serial ClipPRO" no menu Iniciar.
english.PreparacaoFalhou=Setup did not finish. Check the diagnostics to find the step that failed.%nDiagnostics: %1%nYou can also resume with the "Prepare or repair Serial ClipPRO" shortcut in the Start menu.
brazilianportuguese.FinalPendente=Os arquivos foram instalados, mas a preparação ainda está pendente.%nSe houver reinicialização pendente, reinicie o Windows. Depois use "Preparar ou reparar Serial ClipPRO" no menu Iniciar para concluir.
english.FinalPendente=The files were installed, but setup is still pending.%nIf a restart is pending, restart Windows. Then use "Prepare or repair Serial ClipPRO" in the Start menu to finish.

[Types]
Name: "personalizada"; Description: "{cm:TipoPersonalizada}"; Flags: iscustom

[Components]
; Essenciais: sempre instalados, exibidos para o usuário saber o que entra no PC.
Name: "base"; Description: "{cm:CompBase}"; Types: personalizada; Flags: fixed
Name: "base\app"; Description: "{cm:CompApp}"; Types: personalizada; Flags: fixed
Name: "base\ffmpeg"; Description: "{cm:CompFfmpeg}"; Types: personalizada; Flags: fixed; ExtraDiskSpaceRequired: 200000000
Name: "base\ollama"; Description: "{cm:CompOllama}"; Types: personalizada; Flags: fixed; ExtraDiskSpaceRequired: 1500000000
Name: "base\whisper"; Description: "{cm:CompWhisper}"; Types: personalizada; Flags: fixed; ExtraDiskSpaceRequired: 500000000
Name: "base\webview"; Description: "{cm:CompWebview}"; Types: personalizada; Flags: fixed
Name: "base\curl"; Description: "{cm:CompCurl}"; Types: personalizada; Flags: fixed
; Modelos da curadoria: o usuário escolhe; sem escolha, o mais leve. Dá para trocar depois no app.
Name: "modelos"; Description: "{cm:CompModelos}"
Name: "modelos\gemma"; Description: "{cm:CompGemma}"; ExtraDiskSpaceRequired: 8000000000; Flags: dontinheritcheck
Name: "modelos\llama"; Description: "{cm:CompLlama}"; ExtraDiskSpaceRequired: 4900000000; Flags: dontinheritcheck
Name: "modelos\qwen35"; Description: "{cm:CompQwen35}"; ExtraDiskSpaceRequired: 6600000000; Flags: dontinheritcheck
Name: "modelos\qwen3"; Description: "{cm:CompQwen3}"; ExtraDiskSpaceRequired: 9300000000; Flags: dontinheritcheck
Name: "gpu"; Description: "{cm:CompGpu}"; ExtraDiskSpaceRequired: 772000000

[Tasks]
Name: "desktopicon"; Description: "{cm:TarefaAtalho}"; Flags: checkedonce

[Files]
Source: "{#PackageDir}\*"; DestDir: "{app}"; Excludes: "Instalar dependencias.bat,install_prereqs.ps1,LEIA-ME.txt"; Components: base\app; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Components: base\app; Flags: ignoreversion
Source: "..\THIRD_PARTY_LICENSES.md"; DestDir: "{app}"; Components: base\app; Flags: ignoreversion
; Cópia para o link da página de componentes, aberta antes da instalação.
Source: "..\THIRD_PARTY_LICENSES.md"; Flags: dontcopy

[Icons]
Name: "{group}\Serial ClipPRO"; Filename: "{app}\Serial ClipPRO.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Serial ClipPRO"; Filename: "{app}\Serial ClipPRO.exe"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{group}\{cm:AtalhoReparar}"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\bootstrap.ps1"""; WorkingDir: "{app}"; IconFilename: "{app}\Serial ClipPRO.exe"

[InstallDelete]
; Bibliotecas da versão anterior: a pasta é recriada inteira, sem sobras de arquivos que deixaram de existir.
Type: filesandordirs; Name: "{app}\_internal"

[Run]
Filename: "{app}\Serial ClipPRO.exe"; Description: "{cm:AbrirApp}"; Flags: nowait postinstall skipifsilent; Check: PreparationSucceeded
; Atualização pelo app (/SILENT /ATUALIZACAO=1): reabre o app sozinho ao terminar.
Filename: "{app}\Serial ClipPRO.exe"; Flags: nowait; Check: ReabrirAposAtualizacao

[Code]
var
  Ready: Boolean;
  RestartRequired: Boolean;
  StatusBase: String;

function PreparationSucceeded: Boolean;
begin
  Result := Ready and not RestartRequired;
end;

{ Pasta de dados do app (a mesma do bootstrap): CLIPPRO_DATA_DIR ou a padrão. }
function PastaDados: String;
begin
  Result := GetEnv('CLIPPRO_DATA_DIR');
  if Result = '' then
    Result := ExpandConstant('{localappdata}\Serial ClipPRO');
end;

function IdiomaApp: String;
begin
  if ActiveLanguage = 'english' then Result := 'en' else Result := 'pt-BR';
end;

{ O idioma escolhido no instalador vira o do app, a menos que o usuário já tenha escolhido um no app. }
procedure GravarIdiomaApp;
var
  Arquivo: String;
begin
  Arquivo := PastaDados + '\config_interface.json';
  if FileExists(Arquivo) then Exit;
  ForceDirectories(PastaDados);
  SaveStringToFile(Arquivo, '{"idioma": "' + IdiomaApp + '"}', False);
end;

{ Instalação disparada pelo atualizador do app. }
function ModoAtualizacao: Boolean;
begin
  Result := ExpandConstant('{param:atualizacao|0}') = '1';
end;

{ Mesmo se a preparação falhar, o app reabre e mostra o diagnóstico das dependências. }
function ReabrirAposAtualizacao: Boolean;
begin
  Result := ModoAtualizacao and not RestartRequired;
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
  { Licenças de terceiros: abaixo da lista de componentes. }
  Rotulo := TNewStaticText.Create(WizardForm);
  Rotulo.Parent := WizardForm.SelectComponentsPage;
  Rotulo.Caption := CustomMessage('Licencas');
  Rotulo.Left := WizardForm.ComponentsList.Left;
  Rotulo.Top := WizardForm.ComponentsList.Top + WizardForm.ComponentsList.Height + ScaleY(8);
  Link := TNewStaticText.Create(WizardForm);
  Link.Parent := WizardForm.SelectComponentsPage;
  Link.Caption := 'Third Party Licenses';
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
    else if MsgBox(CustomMessage('NenhumModelo'), mbConfirmation, MB_YESNO) = IDYES then
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
  GravarIdiomaApp;
  Parametros := '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\bootstrap.ps1') + '" -SkipLaunch';
  { As mensagens da preparação, mostradas na barra, seguem o idioma do instalador. }
  if ActiveLanguage = 'english' then
    Parametros := Parametros + ' -Idioma en'
  else
    Parametros := Parametros + ' -Idioma pt';
  { Na atualização, o bootstrap roda como reparo: mantém o modelo escolhido no app em vez de voltar ao do instalador. }
  if not ModoAtualizacao then
    Parametros := Parametros + ' -Modelos "' + ModelosEscolhidos + '"';
  if WizardIsComponentSelected('gpu') then
    Parametros := Parametros + ' -Gpu';
  repeat
    StatusBase := CustomMessage('StatusPreparando');
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
    Retry := MsgBox(FmtMessage(CustomMessage('PreparacaoFalhou'), [PastaDados + '\instalacao.log']), mbError, MB_RETRYCANCEL);
  until Retry <> IDRETRY;
end;

{ Tamanho curto à direita de cada item, associado pelo início do nome. }
procedure MostrarTamanhos;
var
  I: Integer;
  Nome, Tamanho: String;
begin
  for I := 0 to WizardForm.ComponentsList.Items.Count - 1 do begin
    Nome := WizardForm.ComponentsList.ItemCaption[I];
    Tamanho := '';
    if Pos('FFmpeg', Nome) = 1 then Tamanho := '191 MB'
    else if Pos('Ollama', Nome) = 1 then Tamanho := '1,4 GB'
    else if Pos('Whisper', Nome) = 1 then Tamanho := '477 MB'
    else if Pos('Gemma 4', Nome) = 1 then Tamanho := '8 GB'
    else if Pos('Llama 3.1', Nome) = 1 then Tamanho := '4,9 GB'
    else if Pos('Qwen 3.5', Nome) = 1 then Tamanho := '6,6 GB'
    else if Pos('Qwen 3 14B', Nome) = 1 then Tamanho := '9,3 GB'
    else if Pos('CUDA', Nome) > 0 then Tamanho := '528 MB';
    if ActiveLanguage = 'english' then
      StringChangeEx(Tamanho, ',', '.', True);
    WizardForm.ComponentsList.ItemSubItem[I] := Tamanho;
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpSelectComponents then
    MostrarTamanhos;
  if (CurPageID = wpFinished) and not Ready then
    WizardForm.FinishedLabel.Caption := CustomMessage('FinalPendente');
end;

function GetCustomSetupExitCode: Integer;
begin
  if RestartRequired then Result := 3010
  else if not Ready then Result := 1
  else Result := 0;
end;
