import os
import shutil
from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bizmanager.settings')

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DB = BASE_DIR / 'db.sqlite3'
DST_DB = Path('/tmp/db.sqlite3')

if os.environ.get('VERCEL'):
    try:
        if not DST_DB.exists() and SRC_DB.exists():
            shutil.copy(SRC_DB, DST_DB)
    except:
        pass

application = get_wsgi_application()
app = application