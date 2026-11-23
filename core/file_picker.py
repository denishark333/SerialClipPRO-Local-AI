"""Seletor nativo para o servidor local no Windows, sem copiar o vídeo."""
import json
import os
import subprocess
import threading
from core.textos import tr

_lock = threading.Lock()


def selecionar_video():
    if os.name != 'nt':
        raise RuntimeError(tr('seletor.windows'))
    if not _lock.acquire(blocking=False):
        raise RuntimeError(tr('seletor.aberto'))
    try:
        script = r'''
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = '__TITULO__'
$dialog.Filter = '__VIDEOS__|*.mp4;*.mkv;*.mov;*.avi;*.webm;*.m4v;*.ts;*.flv|__TODOS__|*.*'
$dialog.Multiselect = $false
try {
    $path = ''
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $path = $dialog.FileName }
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding
    ConvertTo-Json -InputObject $path -Compress
} finally { $dialog.Dispose() }
'''
        # Aspas simples do PowerShell: ' vira ''.
        for marcador, chave in (('__TITULO__', 'seletor.titulo'), ('__VIDEOS__', 'seletor.videos'), ('__TODOS__', 'seletor.todos')):
            script = script.replace(marcador, tr(chave).replace("'", "''"))
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-STA', '-Command', script],
            capture_output=True, encoding='utf-8', check=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return json.loads(result.stdout.strip().lstrip('\ufeff'))
    finally:
        _lock.release()
