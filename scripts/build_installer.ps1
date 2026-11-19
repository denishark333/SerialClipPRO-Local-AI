param(
    [string]$PythonExe = 'build-env\Scripts\python.exe',
    [string]$Compiler = '',
    [switch]$SkipDesktopBuild
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$appVersion = (Get-Content -LiteralPath (Join-Path $projectRoot 'version.json') -Raw | ConvertFrom-Json).version
if (-not $Compiler) {
    $candidates = @(
        (Join-Path $projectRoot 'build-tools\InnoSetup\ISCC.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
        (Join-Path $env:ProgramFiles 'Inno Setup 7\ISCC.exe')
    )
    $Compiler = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $Compiler) { throw 'Inno Setup ausente. Instale o compilador ou informe -Compiler com o caminho de ISCC.exe.' }
}
if (-not $SkipDesktopBuild) {
    & (Join-Path $PSScriptRoot 'build_desktop.ps1') -OutputDir 'dist\v2' -PythonExe $PythonExe
    $pythonPath = if ([IO.Path]::IsPathRooted($PythonExe)) { $PythonExe } else { Join-Path $projectRoot $PythonExe }
    & $pythonPath -m pip freeze | Set-Content -LiteralPath (Join-Path $projectRoot 'dist\v2\Serial ClipPRO\build-packages.txt') -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao registrar pacotes do build.' }
}
$package = Join-Path $projectRoot 'dist\v2\Serial ClipPRO'
if (-not (Test-Path -LiteralPath (Join-Path $package 'Serial ClipPRO.exe'))) { throw 'Build desktop v2 ausente.' }
if (-not (Test-Path -LiteralPath (Join-Path $package 'bootstrap.ps1'))) { throw 'Preparacao ausente no pacote.' }
$output = Join-Path $projectRoot 'dist\installer'
& $Compiler "/DPackageDir=$package" "/DInstallerOutput=$output" "/DAppVersion=$appVersion" (Join-Path $PSScriptRoot 'ClipPro.iss')
if ($LASTEXITCODE -ne 0) { throw 'Falha ao compilar instalador.' }
$installer = Join-Path $output "Serial-ClipPRO-$appVersion-Setup-x64.exe"
(Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash | Set-Content -LiteralPath "$installer.sha256" -Encoding ascii
Write-Host "Instalador: $installer"
