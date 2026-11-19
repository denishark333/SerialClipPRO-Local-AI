param([switch]$LibraryOnly, [switch]$SkipLaunch, [string]$Modelos = '', [switch]$Gpu)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Modelos oferecidos no instalador, na ordem de preferencia do app (Recomendado, Leve,
# Intermediario, Experimental). O primeiro escolhido vira o modelo da curadoria.
$script:CatalogoModelos = [ordered]@{
    'gemma4:12b' = 'Gemma 4 12B'
    'llama3.1'   = 'Llama 3.1 8B'
    'qwen3.5:9b' = 'Qwen 3.5 9B'
    'qwen3:14b'  = 'Qwen 3 14B'
}
$script:ModeloPadrao = 'llama3.1'
# Aceleracao NVIDIA: o CTranslate2 ja traz o cuDNN; o Whisper so precisa destes dois
# arquivos do cuBLAS, extraidos do pacote oficial da NVIDIA no PyPI (hash fixo).
$script:CublasUrl = 'https://files.pythonhosted.org/packages/20/e2/fc9a0e985249d873150276d5afb02e39a66817fedbf1a385724393e505ed/nvidia_cublas_cu12-12.9.2.10-py3-none-win_amd64.whl'
$script:CublasSha256 = '623F43027D40D44CEADF0043F002BD25CF353E8F13CE90B9A87057019F560661'
$script:CublasArquivos = @('cublas64_12.dll', 'cublasLt64_12.dll')

function Write-Progresso($Percent, $Message) {
    # Linha lida pelo instalador para mover a barra; no console, so a mensagem aparece em destaque.
    Write-Host $Message -ForegroundColor Cyan
    [Console]::Out.WriteLine("@@PROGRESSO|$([int]$Percent)|$Message")
    [Console]::Out.Flush()
}
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
function Resolve-Modelos($Lista, $DataDir) {
    $escolhidos = @($Lista -split '[,;\s]+' | Where-Object { $_ -match '^[A-Za-z0-9._:/-]+$' } | Select-Object -Unique)
    if ($escolhidos.Count) { return ,$escolhidos }
    # Reparo sem escolha: mantem o modelo ja configurado no app ou usa o mais leve.
    $config = Join-Path $DataDir 'config_ia.json'
    try {
        $atual = (Get-Content -LiteralPath $config -Raw -ErrorAction Stop | ConvertFrom-Json).modelo
        if ($atual -match '^[A-Za-z0-9._:/-]+$') { return ,@($atual) }
    } catch {}
    return ,@($script:ModeloPadrao)
}
function Select-ModeloPrincipal($Escolhidos) {
    foreach ($nome in $script:CatalogoModelos.Keys) { if ($Escolhidos -contains $nome) { return $nome } }
    return $Escolhidos[0]
}
function Save-ConfigIa($DataDir, $Modelo) {
    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
    # Sem BOM: o app le o arquivo como JSON UTF-8 puro.
    [IO.File]::WriteAllText((Join-Path $DataDir 'config_ia.json'), (@{ modelo = $Modelo } | ConvertTo-Json -Compress), (New-Object Text.UTF8Encoding($false)))
}
function Get-NomeModelo($Nome) {
    if ($script:CatalogoModelos.Contains($Nome)) { return $script:CatalogoModelos[$Nome] }
    return $Nome
}
function Test-ModeloInstalado($Tags, $Nome) {
    $base = if ($Nome -like '*:*') { $Nome } else { "${Nome}:latest" }
    return [bool]($Tags.models | Where-Object { $_.name -eq $base })
}
function Invoke-OllamaPull($Nome, $Inicio, $Fim) {
    # A API do Ollama informa bytes recebidos: a barra do instalador mostra o avanco real.
    $rotulo = Get-NomeModelo $Nome
    $request = [Net.HttpWebRequest]::Create('http://127.0.0.1:11434/api/pull')
    $request.Method = 'POST'
    $request.ContentType = 'application/json'
    $request.Timeout = 60000
    $request.ReadWriteTimeout = 600000
    $corpo = [Text.Encoding]::UTF8.GetBytes((@{ model = $Nome; stream = $true } | ConvertTo-Json -Compress))
    $stream = $request.GetRequestStream(); $stream.Write($corpo, 0, $corpo.Length); $stream.Close()
    try { $response = $request.GetResponse() }
    catch [Net.WebException] {
        $detalhe = ''
        if ($_.Exception.Response) { $detalhe = (New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())).ReadToEnd() }
        throw "Download de $rotulo recusado pelo Ollama: $detalhe"
    }
    $reader = New-Object IO.StreamReader($response.GetResponseStream())
    $ultimo = -1
    try {
        while (-not $reader.EndOfStream) {
            $linha = $reader.ReadLine()
            if (-not $linha) { continue }
            $evento = $linha | ConvertFrom-Json
            if ($evento.error) { throw "Download de ${rotulo}: $($evento.error)" }
            if ($evento.total -and $evento.completed) {
                $pct = [int]($Inicio + ($Fim - $Inicio) * $evento.completed / $evento.total)
                if ($pct -ne $ultimo) {
                    $ultimo = $pct
                    $feito = '{0:N1}' -f ($evento.completed / 1GB); $total = '{0:N1}' -f ($evento.total / 1GB)
                    Write-Progresso $pct "Baixando $rotulo ($feito de $total GB)..."
                }
            }
        }
    } finally { $reader.Close(); $response.Close() }
}
function Install-Ollama($Cache) {
    $installer = Join-Path $Cache 'OllamaSetup.exe'
    Get-Download 'https://ollama.com/download/OllamaSetup.exe' $installer
    Assert-SignedInstaller $installer 'Ollama'
    Invoke-Installer $installer '/SP- /VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
    Refresh-Path
    if (-not (Test-Command ollama)) { throw 'Ollama nao foi encontrado apos instalar.' }
}
function Wait-Ollama($DataDir) {
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        try { return Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2 }
        catch {
            if ($attempt -eq 0) {
                Start-Process -FilePath (Get-Command ollama).Source -ArgumentList 'serve' -WindowStyle Hidden -RedirectStandardOutput (Join-Path $DataDir 'ollama-setup.log') -RedirectStandardError (Join-Path $DataDir 'ollama-setup-error.log')
            }
            Start-Sleep -Seconds 1
        }
    }
    throw 'Ollama nao respondeu. Execute o instalador novamente para tentar retomar.'
}
function Install-Modelo($Nome, $Inicio, $Fim, $Cache, $DataDir) {
    try { Invoke-OllamaPull $Nome $Inicio $Fim }
    catch {
        # Modelos novos (como o Gemma 4) exigem um Ollama recente: atualiza e tenta de novo.
        if ($_.Exception.Message -notmatch '(?i)newer version|update ollama|upgrade') { throw }
        Write-Progresso $Inicio "Atualizando o Ollama para baixar $(Get-NomeModelo $Nome)..."
        Get-Process ollama* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Install-Ollama $Cache
        Wait-Ollama $DataDir | Out-Null
        Invoke-OllamaPull $Nome $Inicio $Fim
    }
    & ollama show $Nome | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Modelo $(Get-NomeModelo $Nome) nao passou na verificacao." }
}
function Get-DownloadProgresso($Url, $Destination, $Inicio, $Fim, $Rotulo) {
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            $response = [Net.HttpWebRequest]::Create($Url).GetResponse()
            $total = $response.ContentLength
            $entrada = $response.GetResponseStream()
            $saida = [IO.File]::Create("$Destination.partial")
            try {
                $buffer = New-Object byte[] (1MB); $lidos = 0L; $ultimo = -1
                while (($n = $entrada.Read($buffer, 0, $buffer.Length)) -gt 0) {
                    $saida.Write($buffer, 0, $n); $lidos += $n
                    if ($total -gt 0) {
                        $pct = [int]($Inicio + ($Fim - $Inicio) * $lidos / $total)
                        if ($pct -ne $ultimo) { $ultimo = $pct; Write-Progresso $pct ("$Rotulo ({0:N0} de {1:N0} MB)..." -f ($lidos / 1MB), ($total / 1MB)) }
                    }
                }
            } finally { $saida.Close(); $entrada.Close(); $response.Close() }
            Move-Item -LiteralPath "$Destination.partial" -Destination $Destination -Force
            return
        } catch {
            if ($attempt -eq 3) { throw }
            Start-Sleep -Seconds 2
        }
    }
}
function Install-Cuda($Cache, $DataDir, $Inicio, $Fim) {
    $destino = Join-Path $DataDir 'tools\cuda'
    $faltando = @($script:CublasArquivos | Where-Object { -not (Test-Path -LiteralPath (Join-Path $destino $_)) })
    if (-not $faltando.Count) { return }
    $wheel = Join-Path $Cache 'nvidia-cublas.whl'
    Get-DownloadProgresso $script:CublasUrl $wheel $Inicio $Fim 'Baixando aceleracao NVIDIA'
    if ((Get-FileHash -LiteralPath $wheel -Algorithm SHA256).Hash -ne $script:CublasSha256) {
        Remove-Item -LiteralPath $wheel -Force
        throw 'Download da aceleracao NVIDIA falhou na verificacao SHA256. Execute novamente.'
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    New-Item -ItemType Directory -Path $destino -Force | Out-Null
    $zip = [IO.Compression.ZipFile]::OpenRead($wheel)
    try {
        foreach ($arquivo in $script:CublasArquivos) {
            $entrada = $zip.Entries | Where-Object { $_.FullName.Replace([char]92, [char]47) -eq "nvidia/cublas/bin/$arquivo" } | Select-Object -First 1
            if (-not $entrada) { throw "Pacote NVIDIA nao contem $arquivo." }
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entrada, (Join-Path $destino $arquivo), $true)
        }
    } finally { $zip.Dispose() }
    Remove-Item -LiteralPath $wheel -Force
}
function Install-ClipPro {
    param([string]$Modelos = '', [switch]$Gpu)
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
        Write-Progresso 1 'Preparando arquivos do aplicativo...'
        Unblock-Package $package
        Refresh-Path
        Write-Progresso 3 'Verificando .NET Framework e Visual C++...'
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
        Write-Progresso 8 'Preparando FFmpeg...'
        Install-FFmpeg $cache $data
        foreach ($command in @('ffmpeg', 'ffprobe')) {
            Test-MediaRuntime $command
        }
        Write-Progresso 13 'Verificando WebView2...'
        if (-not (Test-WebView)) {
            $installer = Join-Path $cache 'WebView2Setup.exe'
            Get-Download 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' $installer
            Assert-SignedInstaller $installer 'Microsoft Corporation'
            Invoke-Installer $installer '/silent /install'
            if (-not (Test-WebView)) { throw 'WebView2 nao foi detectado apos instalar.' }
        }
        Write-Progresso 16 'Preparando Ollama...'
        Write-Host 'Se aparecer a janela inicial do Ollama, prossiga e escolha o uso local. Nao e necessario usar modelos cloud para o ClipPRO.'
        if (-not (Test-Command ollama)) { Install-Ollama $cache }
        $tags = Wait-Ollama $data
        if ($Gpu) {
            Write-Progresso 22 'Preparando aceleracao NVIDIA...'
            Install-Cuda $cache $data 22 34
        }
        $escolhidos = Resolve-Modelos $Modelos $data
        $faixa = 54 / $escolhidos.Count
        for ($i = 0; $i -lt $escolhidos.Count; $i++) {
            $nome = $escolhidos[$i]
            $inicio = 35 + $faixa * $i
            Write-Progresso $inicio "Verificando $(Get-NomeModelo $nome)..."
            if (Test-ModeloInstalado $tags $nome) {
                & ollama show $nome | Out-Null
                if ($LASTEXITCODE -eq 0) { continue }
            }
            Install-Modelo $nome $inicio ($inicio + $faixa) $cache $data
        }
        # A escolha feita no instalador define o modelo da curadoria; o reparo preserva a do app.
        if ($Modelos -or -not (Test-Path -LiteralPath (Join-Path $data 'config_ia.json'))) {
            Save-ConfigIa $data (Select-ModeloPrincipal $escolhidos)
        }
        if ($script:RestartRequired) {
            Write-Host 'O Windows solicitou reinicializacao. Reinicie e use Preparar ou reparar Serial ClipPRO no menu Iniciar para concluir.' -ForegroundColor Yellow
            return 3010
        }
        Write-Progresso 90 'Testando o aplicativo...'
        $app = Join-Path $package 'Serial ClipPRO.exe'
        $env:CLIPPRO_DATA_DIR = $data
        $process = Wait-AppSetup $app '--self-test' 'Verificando o aplicativo'
        if ($process.ExitCode -ne 0) { throw "Teste do aplicativo falhou. Diagnostico: $(Join-Path $data 'self-test.json')" }
        Write-Progresso 94 'Preparando o Whisper (transcricao das falas)...'
        Write-Host "Detalhes: $(Join-Path $data 'models-setup.log')"
        $process = Wait-AppSetup $app '--prepare-models' 'Preparando Whisper'
        if ($process.ExitCode -ne 0) { throw "Preparacao do Whisper falhou. Diagnostico: $(Join-Path $data 'models-setup.json'). Execute novamente para retomar." }
        Write-Progresso 100 'Preparacao concluida. Todos os testes passaram.'
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
    try { exit (Install-ClipPro -Modelos $Modelos -Gpu:$Gpu) }
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
