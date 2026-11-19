param([string]$OutputDir = 'dist', [string]$PythonExe = 'venv\Scripts\python.exe')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = if ([IO.Path]::IsPathRooted($PythonExe)) { $PythonExe } else { Join-Path $projectRoot $PythonExe }
& $pythonPath -c "import sys; assert sys.version_info.releaselevel == 'final', 'Build requer Python estavel'; assert sys.maxsize > 2**32, 'Build requer Python x64'"
if ($LASTEXITCODE -ne 0) { throw 'Python de build precisa ser estavel e x64. Informe -PythonExe.' }
Push-Location (Join-Path $projectRoot 'frontend')
try {
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Falha no build do frontend.' }
} finally { Pop-Location }
Push-Location $projectRoot
try {
    $outputRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot $OutputDir))
    if (-not $outputRoot.StartsWith($projectRoot.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'A pasta de build precisa estar dentro do projeto.' }
    & $pythonPath -m PyInstaller --noconfirm --distpath $outputRoot ClipPro.spec
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao empacotar desktop.' }
    $packageDir = Join-Path $outputRoot 'Serial ClipPRO'
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'install_prereqs.ps1') -Destination $packageDir
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'bootstrap.ps1') -Destination $packageDir
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Instalar dependencias.bat') -Destination $packageDir
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'LEIA-ME.txt') -Destination $packageDir
    Write-Host "Distribua a pasta inteira: $packageDir"
} finally { Pop-Location }
