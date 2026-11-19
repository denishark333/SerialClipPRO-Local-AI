import json
from core.config import BASE_DIR

APP_VERSION = json.loads((BASE_DIR / 'version.json').read_text(encoding='utf-8'))['version']
