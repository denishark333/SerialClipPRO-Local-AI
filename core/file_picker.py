"""Seletor nativo para o servidor local no Windows, sem copiar o vídeo."""
import json
import os
import subprocess
import threading

_lock = threading.Lock()


def selecionar_video():
    if os.name != 'nt':
        raise RuntimeError('O seletor local requer Windows.')
    if not _lock.acquire(blocking=False):
        raise RuntimeError('Já existe um seletor de arquivos aberto.')
    try:
        script = r'''
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = 'Selecionar vídeo — Serial ClipPRO'
$dialog.Filter = 'Vídeos|*.mp4;*.mkv;*.mov;*.avi;*.webm;*.m4v;*.ts;*.flv|Todos os arquivos|*.*'
$dialog.Multiselect = $false
try {
    $path = ''
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $path = $dialog.FileName }
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding
    ConvertTo-Json -InputObject $path -Compress
} finally { $dialog.Dispose() }
'''
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-STA', '-Command', script],
            capture_output=True, encoding='utf-8', check=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return json.loads(result.stdout.strip().lstrip('\ufeff'))
    finally:
        _lock.release()
