from pathlib import Path
import json
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
root = Path(SPECPATH)
app_version = json.loads((root / 'version.json').read_text(encoding='utf-8'))['version']
version_numbers = tuple(int(part) for part in app_version.split('.')) + (0,)
version_file = root / 'build' / 'version_info.txt'
version_file.parent.mkdir(exist_ok=True)
version_file.write_text((root / 'scripts/version_info.txt').read_text(encoding='utf-8').replace('2.0.0', app_version).replace('(2, 0, 0, 0)', str(version_numbers)), encoding='utf-8')
if not (root / 'frontend/dist/index.html').is_file():
    raise SystemExit('Compile o frontend antes: npm.cmd run build')
# curl_cffi (acesso à Kick): o módulo carrega a libcurl-impersonate de curl_cffi.libs, fora do pacote.
import curl_cffi
curl_libs = Path(curl_cffi.__file__).resolve().parent.parent / 'curl_cffi.libs'
binaries_curl = [(str(dll), 'curl_cffi.libs') for dll in curl_libs.glob('*.dll')]
if not binaries_curl:
    raise SystemExit('curl_cffi.libs ausente: instale curl_cffi>=0.10,<0.17 no ambiente de build.')
a = Analysis([str(root / 'desktop.py')], pathex=[str(root)],
    binaries=collect_dynamic_libs('ctranslate2') + binaries_curl,
    datas=[(str(root / 'version.json'), '.'), (str(root / 'frontend/dist'), 'frontend/dist'), (str(root / 'assets/fonts'), 'assets/fonts')] + collect_data_files('faster_whisper') + collect_data_files('webview'),
    hiddenimports=['uvicorn.logging', 'uvicorn.loops.auto', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan.on', 'curl_cffi', 'yt_dlp.networking._curlcffi'],
    excludes=['torch', 'gradio', 'IPython', 'pytest'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Serial ClipPRO', console=False, icon=str(root / 'assets/serial-clippro.ico'), version=str(version_file))
coll = COLLECT(exe, a.binaries, a.datas, name='Serial ClipPRO')
