param([switch]$LibraryOnly, [switch]$SkipLaunch)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Get-DataDir {
    if ($env:CLIPPRO_DATA_DIR) { return [IO.Path]::GetFullPath($env:CLIPPRO_DATA_DIR) }
    return Join-Path $env:LOCALAPPDATA 'Serial ClipPRO'
}
function Refresh-Path {
    $tools = Join-Path (Get-DataDir) 'tools\ffmpeg'
    $ollama = Join-Path $env:LOCALAPPDATA 'Programs\Ollama'
    $env:Path = "$tools;$ollama;" + [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}
function Test-Command($Name) { return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue) }
function Test-MediaRuntime($Command) {
    # Consome toda a saida: Select-Object -First no processo fecha o pipe cedo.
    $versionOutput = @(& $Command -version)
    $versionExitCode = $LASTEXITCODE
    $versionOutput | Select-Object -First 1 | Out-Host
    if ($versionExitCode -ne 0) { throw "$Command nao executou corretamente (codigo $versionExitCode)." }
}
function Get-Download($Url, $Destination) {
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            Write-Host "Baixando $(Split-Path $Destination -Leaf), tentativa $attempt/3..."
            if (Test-Command curl.exe) {
                & curl.exe --fail --location --retry 2 --connect-timeout 30 --output "$Destination.partial" $Url
                if ($LASTEXITCODE -ne 0) { throw "Falha de download (curl $LASTEXITCODE)." }
            } else {
                Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile "$Destination.partial" -TimeoutSec 7200
            }
            if ((Get-Item -LiteralPath "$Destination.partial").Length -eq 0) { throw 'Download vazio.' }
            Move-Item -LiteralPath "$Destination.partial" -Destination $Destination -Force
            return
        } catch {
            if ($attempt -eq 3) { throw }
            Start-Sleep -Seconds 2
        }
    }
}
function Assert-SignedInstaller($File, $Publisher) {
    $signature = Get-AuthenticodeSignature -LiteralPath $File
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch $Publisher) {
        throw "Assinatura do instalador nao confere: $File. Instalacao interrompida."
    }
}
function Invoke-Installer($File, $Arguments, [switch]$Elevate) {
    $params = @{ FilePath = $File; ArgumentList = $Arguments; PassThru = $true; Wait = $true; WindowStyle = 'Hidden' }
    if ($Elevate) {
        $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
        if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { $params.Verb = 'RunAs' }
    }
    $process = Start-Process @params
    if ($process.ExitCode -in @(3010, 1641)) { $script:RestartRequired = $true; return }
    if ($process.ExitCode -ne 0) { throw "Instalador $(Split-Path $File -Leaf) falhou (codigo $($process.ExitCode))." }
}
function Test-WebView {
    $key = 'Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
    foreach ($root in @('HKLM:\SOFTWARE\WOW6432Node', 'HKLM:\SOFTWARE', 'HKCU:\SOFTWARE')) {
        $version = (Get-ItemProperty -LiteralPath "$root\$key" -ErrorAction SilentlyContinue).pv
        if ($version -and $version -ne '0.0.0.0') { return $true }
    }
    return $false
}
function Test-NetFramework {
    $release = (Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full' -ErrorAction SilentlyContinue).Release
    return $release -ge 528040
}
function Test-VCRuntime {
    foreach ($root in @('HKLM:\SOFTWARE\Microsoft', 'HKLM:\SOFTWARE\WOW6432Node\Microsoft')) {
        if ((Get-ItemProperty -LiteralPath "$root\VisualStudio\14.0\VC\Runtimes\x64" -ErrorAction SilentlyContinue).Installed -eq 1) { return $true }
    }
    return $false
}
function Unblock-Package($PackageRoot) {
    $resolved = [IO.Path]::GetFullPath($PackageRoot).TrimEnd('\')
    if (-not (Test-Path -LiteralPath (Join-Path $resolved 'Serial ClipPRO.exe'))) { throw 'Pasta do pacote invalida.' }
    Unblock-File -LiteralPath (Join-Path $resolved 'Serial ClipPRO.exe')
    $internal = Join-Path $resolved '_internal'
    if (Test-Path -LiteralPath $internal) {
        Get-ChildItem -LiteralPath $internal -Recurse -File | Where-Object { $_.Extension -in @('.dll', '.pyd', '.exe') } | ForEach-Object {
            if (-not $_.FullName.StartsWith($resolved + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Arquivo fora do pacote.' }
            Unblock-File -LiteralPath $_.FullName
        }
    }
}
function Install-FFmpeg($Cache, $DataDir) {
    if ((Test-Command ffmpeg) -and (Test-Command ffprobe)) { return }
    $zip = Join-Path $Cache 'ffmpeg.zip'
    $hashFile = Join-Path $Cache 'ffmpeg.sha256'
    Get-Download 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' $zip
    Get-Download 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip.sha256' $hashFile
    $hashText = Get-Content -LiteralPath $hashFile -Raw
    if ($hashText -notmatch '(?i)\b[0-9a-f]{64}\b') { throw 'Checksum do FFmpeg invalido.' }
    $expected = $Matches[0]
    if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash -ne $expected) { throw 'Download do FFmpeg falhou na verificacao SHA256. Execute novamente.' }
    $extracted = Join-Path $Cache ('ffmpeg-' + [Guid]::NewGuid().ToString('N'))
    Expand-Archive -LiteralPath $zip -DestinationPath $extracted
    $destination = Join-Path $DataDir 'tools\ffmpeg'
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    foreach ($binary in @('ffmpeg.exe', 'ffprobe.exe')) {
        $source = @(Get-ChildItem -LiteralPath $extracted -Recurse -File -Filter $binary)
        if ($source.Count -ne 1) { throw "Pacote FFmpeg nao contem $binary." }
        Copy-Item -LiteralPath $source[0].FullName -Destination (Join-Path $destination $binary) -Force
        Unblock-File -LiteralPath (Join-Path $destination $binary)
    }
    Refresh-Path
}
function Install-ClipPro {
    if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { throw 'Este pacote requer Windows x64.' }
    $package = $PSScriptRoot
    if (-not (Test-Path -LiteralPath (Join-Path $package 'Serial ClipPRO.exe'))) {
        $package = Join-Path (Split-Path $PSScriptRoot -Parent) 'dist\Serial ClipPRO'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $package 'Serial ClipPRO.exe'))) { throw 'Extraia a pasta inteira do ZIP. Executavel nao encontrado.' }
    $data = Get-DataDir
    $cache = Join-Path $data 'setup-cache'
    New-Item -ItemType Directory -Path $cache -Force | Out-Null
    Start-Transcript -LiteralPath (Join-Path $data 'instalacao.log') -Append | Out-Null
    $script:RestartRequired = $false
    try {
        Write-Host '[1/7] Preparando arquivos do aplicativo...' -ForegroundColor Cyan
        Unblock-Package $package
        Refresh-Path
        Write-Host '[2/7] Verificando .NET Framework e Visual C++...' -ForegroundColor Cyan
        if (-not (Test-NetFramework)) {
            $installer = Join-Path $cache 'dotnet48.exe'
            Get-Download 'https://go.microsoft.com/fwlink/?linkid=2088631' $installer
            Assert-SignedInstaller $installer 'Microsoft Corporation'
            Invoke-Installer $installer '/q /norestart' -Elevate
            if (-not (Test-NetFramework) -and -not $script:RestartRequired) { throw '.NET Framework nao foi detectado apos instalar.' }
        }
        if (-not (Test-VCRuntime)) {
            $installer = Join-Path $cache 'vc_redist.x64.exe'
            Get-Download 'https://aka.ms/vc14/vc_redist.x64.exe' $installer
            Assert-SignedInstaller $installer 'Microsoft Corporation'
            Invoke-Installer $installer '/install /quiet /norestart' -Elevate
            if (-not (Test-VCRuntime) -and -not $script:RestartRequired) { throw 'Visual C++ nao foi detectado apos instalar.' }
        }
        Write-Host '[3/7] Preparando FFmpeg e ffprobe...' -ForegroundColor Cyan
        Install-FFmpeg $cache $data
        foreach ($command in @('ffmpeg', 'ffprobe')) {
            Test-MediaRuntime $command
        }
        Write-Host '[4/7] Verificando WebView2...' -ForegroundColor Cyan
        if (-not (Test-WebView)) {
            $installer = Join-Path $cache 'WebView2Setup.exe'
            Get-Download 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' $installer
            Assert-SignedInstaller $installer 'Microsoft Corporation'
            Invoke-Installer $installer '/silent /install'
            if (-not (Test-WebView)) { throw 'WebView2 nao foi detectado apos instalar.' }
        }
        Write-Host '[5/7] Preparando Ollama...' -ForegroundColor Cyan
        Write-Host 'Se aparecer a janela inicial do Ollama, prossiga e escolha o uso local. Nao e necessario usar modelos cloud para o ClipPRO.'
        if (-not (Test-Command ollama)) {
            $installer = Join-Path $cache 'OllamaSetup.exe'
            Get-Download 'https://ollama.com/download/OllamaSetup.exe' $installer
            Assert-SignedInstaller $installer 'Ollama'
            Invoke-Installer $installer '/SP- /VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
            Refresh-Path
            if (-not (Test-Command ollama)) { throw 'Ollama nao foi encontrado apos instalar.' }
        }
        $ready = $false
        for ($attempt = 0; $attempt -lt 60; $attempt++) {
            try {
                $tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2
                $ready = $true
                break
            } catch {
                if ($attempt -eq 0) {
                    Start-Process -FilePath (Get-Command ollama).Source -ArgumentList 'serve' -WindowStyle Hidden -RedirectStandardOutput (Join-Path $data 'ollama-setup.log') -RedirectStandardError (Join-Path $data 'ollama-setup-error.log')
                }
                Start-Sleep -Seconds 1
            }
        }
        if (-not $ready) { throw 'Ollama nao respondeu. Execute o instalador novamente para tentar retomar.' }
        Write-Host '[6/7] Baixando/verificando Llama 3.1 (varios GB)...' -ForegroundColor Cyan
        if (-not ($tags.models | Where-Object { $_.name -eq 'llama3.1:latest' })) {
            & ollama pull llama3.1 | Out-Host
            if ($LASTEXITCODE -ne 0) { throw 'Download do Llama interrompido. Execute novamente para retomar.' }
        }
        & ollama show llama3.1 | Out-Host
        if ($LASTEXITCODE -ne 0) { throw 'Modelo Llama nao passou na verificacao.' }
        if ($script:RestartRequired) {
            Write-Host 'O Windows solicitou reinicializacao. Reinicie e use Preparar ou reparar Serial ClipPRO no menu Iniciar para concluir.' -ForegroundColor Yellow
            return 3010
        }
        Write-Host '[7/7] Testando runtime e preparando Whisper small...' -ForegroundColor Cyan
        $app = Join-Path $package 'Serial ClipPRO.exe'
        $env:CLIPPRO_DATA_DIR = $data
        $process = Wait-AppSetup $app '--self-test' 'Verificando o aplicativo'
        if ($process.ExitCode -ne 0) { throw "Teste do aplicativo falhou. Diagnostico: $(Join-Path $data 'self-test.json')" }
        Write-Host 'Preparando Whisper: pode baixar arquivos na primeira vez. O tempo depende da conexao.'
        Write-Host "Detalhes: $(Join-Path $data 'models-setup.log')"
        $process = Wait-AppSetup $app '--prepare-models' 'Preparando Whisper'
        if ($process.ExitCode -ne 0) { throw "Preparacao do Whisper falhou. Diagnostico: $(Join-Path $data 'models-setup.json'). Execute novamente para retomar." }
        Write-Host 'Preparacao concluida. Todos os testes passaram.' -ForegroundColor Green
        if (-not $SkipLaunch) { Start-Process -FilePath $app -WindowStyle Hidden }
        return 0
    } finally { Stop-Transcript | Out-Null }
}
function Wait-AppSetup($AppPath, $Argument, $Label) {
    $process = Start-Process -FilePath $AppPath -ArgumentList $Argument -WindowStyle Hidden -PassThru
    $started = Get-Date
    while (-not $process.WaitForExit(10000)) {
        $seconds = [int]((Get-Date) - $started).TotalSeconds
        Write-Host "$Label - processo ainda em execucao ($seconds segundos). Aguarde."
    }
    return $process
}

if (-not $LibraryOnly) {
    try { exit (Install-ClipPro) }
    catch {
        $failureLog = Join-Path (Get-DataDir) 'instalacao.log'
        if (Test-Path -LiteralPath (Split-Path $failureLog -Parent)) {
            ('FALHA: ' + $_.Exception.Message) | Out-File -LiteralPath $failureLog -Append -Encoding utf8
        }
        Write-Host $_.Exception.Message -ForegroundColor Red
        Write-Host 'Retome pelo instalador ou pelo atalho Preparar ou reparar Serial ClipPRO no menu Iniciar.'
        exit 1
    }
}
